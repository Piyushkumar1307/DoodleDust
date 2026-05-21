"""Stable Diffusion + ControlNet with quality vs live (LCM) profiles."""

from __future__ import annotations

import logging
import threading
from typing import Literal, Optional, Tuple

import torch
from PIL import Image

from config import settings

logger = logging.getLogger(__name__)

Profile = Literal["live", "quality"]

DEFAULT_NEGATIVE = (
    "low quality, blurry, distorted, deformed, ugly, bad anatomy, watermark, text, "
    "wrong composition, ignoring sketch, unrelated scene, aerial drone view, "
    "bird's eye view, different layout"
)

LIVE_NEGATIVE = (
    "low quality, blurry, ugly, watermark, text, wrong composition, aerial drone view"
)


def _resolve_device() -> Tuple[str, torch.dtype]:
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32


class GenerationPipeline:
    _instance: Optional["GenerationPipeline"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._pipe = None
        self._device, self._dtype = _resolve_device()
        self._ready = threading.Event()
        self._live_ready = False
        self._live_use_lcm = False
        self._default_scheduler = None

    @classmethod
    def get(cls) -> "GenerationPipeline":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @property
    def device(self) -> str:
        return self._device

    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()

    def load(self) -> None:
        if self._pipe is not None:
            return

        with self._lock:
            if self._pipe is not None:
                return

            logger.info("Loading models on %s (%s)...", self._device, self._dtype)
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

            controlnet = ControlNetModel.from_pretrained(
                settings.controlnet_model_id,
                torch_dtype=self._dtype,
            )

            pipe = StableDiffusionControlNetPipeline.from_pretrained(
                settings.sd_model_id,
                controlnet=controlnet,
                torch_dtype=self._dtype,
                safety_checker=None,
            )

            pipe.set_progress_bar_config(disable=True)
            self._default_scheduler = pipe.scheduler

            if self._device == "cuda":
                pipe.to("cuda")
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    logger.debug("xformers not available")
            elif self._device == "mps":
                pipe.to("mps")
                pipe.vae.to(dtype=torch.float32)
                pipe.enable_attention_slicing()
            else:
                pipe.enable_attention_slicing()
                pipe.enable_model_cpu_offload()

            self._pipe = pipe
            self._ready.set()
            logger.info("Models ready on %s.", self._device)

    def _ensure_live_mode(self) -> None:
        """Fast Doodle Dust AI: LCM LoRA if PEFT works, else fewer steps without LoRA."""
        if self._live_ready or self._pipe is None:
            return

        try:
            import peft  # noqa: F401
            from diffusers.utils import USE_PEFT_BACKEND

            if not USE_PEFT_BACKEND:
                raise RuntimeError("diffusers USE_PEFT_BACKEND is False")

            from diffusers import LCMScheduler

            logger.info("Loading LCM LoRA for fast Doodle Dust AI...")
            self._pipe.load_lora_weights(settings.lcm_lora_id)
            if hasattr(self._pipe, "fuse_lora"):
                self._pipe.fuse_lora()
            self._pipe.scheduler = LCMScheduler.from_config(
                self._pipe.scheduler.config
            )
            self._live_use_lcm = True
            logger.info("LCM fast mode ready.")
        except Exception as exc:
            logger.warning(
                "LCM/PEFT unavailable (%s) — using reduced-step fast mode. "
                "For best speed run: pip install -U peft && restart backend",
                exc,
            )
            self._restore_quality_scheduler()
            self._live_use_lcm = False

        self._live_ready = True

    def _restore_quality_scheduler(self) -> None:
        if self._pipe is None or self._default_scheduler is None:
            return
        self._pipe.scheduler = self._default_scheduler

    @torch.inference_mode()
    def generate(
        self,
        sketch: Image.Image,
        prompt: str,
        *,
        profile: Profile = "quality",
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        controlnet_scale: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Image.Image:
        self.load()
        assert self._pipe is not None

        if profile == "live":
            self._ensure_live_mode()
            width = width or settings.live_width
            height = height or settings.live_height
            negative_prompt = LIVE_NEGATIVE
            if self._live_use_lcm:
                steps = steps or settings.live_steps
                guidance_scale = guidance_scale or settings.live_guidance_scale
            else:
                steps = steps or max(settings.live_steps, 6)
                guidance_scale = guidance_scale or settings.guidance_scale
            controlnet_scale = controlnet_scale or settings.live_controlnet_scale
        else:
            self._restore_quality_scheduler()
            steps = steps or settings.inference_steps
            guidance_scale = guidance_scale or settings.guidance_scale
            controlnet_scale = controlnet_scale or settings.controlnet_scale
            width = width or settings.preview_width
            height = height or settings.preview_height

        gen_device = "cpu" if self._device == "mps" else self._device
        generator = None
        if seed is not None:
            generator = torch.Generator(device=gen_device).manual_seed(seed)

        result = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=sketch,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=controlnet_scale,
            generator=generator,
            width=width,
            height=height,
            output_type="pil",
        )

        image = result.images[0].convert("RGB")

        import numpy as np

        if float(np.array(image).mean()) < 4.0:
            logger.warning("Nearly black output on %s (profile=%s)", self._device, profile)

        return image
