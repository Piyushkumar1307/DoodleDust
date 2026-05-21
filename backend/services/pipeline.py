"""Local Stable Diffusion + ControlNet (scribble). Zero API cost."""

from __future__ import annotations

import logging
import threading
from typing import Optional, Tuple

import torch
from PIL import Image

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_NEGATIVE = (
    "low quality, blurry, distorted, deformed, ugly, bad anatomy, watermark, text, "
    "wrong composition, ignoring sketch, unrelated scene, aerial drone view, "
    "bird's eye view, different layout"
)


def _resolve_device() -> Tuple[str, torch.dtype]:
    """CUDA > Apple MPS > CPU. MPS must use float32 — float16 VAE outputs black images."""
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", torch.float32
    return "cpu", torch.float32


class GenerationPipeline:
    """Singleton pipeline — load once, reuse across requests."""

    _instance: Optional["GenerationPipeline"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._pipe = None
        self._device, self._dtype = _resolve_device()
        self._ready = threading.Event()

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

            if self._device == "cuda":
                pipe.to("cuda")
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                except Exception:
                    logger.debug("xformers not available, using default attention")
            elif self._device == "mps":
                pipe.to("mps")
                # VAE in fp16 on MPS decodes to solid black — keep VAE in fp32
                pipe.vae.to(dtype=torch.float32)
                pipe.enable_attention_slicing()
            else:
                pipe.enable_attention_slicing()
                pipe.enable_model_cpu_offload()

            self._pipe = pipe
            self._ready.set()
            logger.info("Models ready on %s.", self._device)

    @torch.inference_mode()
    def generate(
        self,
        sketch: Image.Image,
        prompt: str,
        *,
        negative_prompt: str = DEFAULT_NEGATIVE,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        controlnet_scale: Optional[float] = None,
    ) -> Image.Image:
        self.load()
        assert self._pipe is not None

        steps = steps or settings.inference_steps
        guidance_scale = guidance_scale or settings.guidance_scale
        controlnet_scale = controlnet_scale or settings.controlnet_scale

        # MPS generator must use CPU for some torch versions
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
            width=settings.preview_width,
            height=settings.preview_height,
            output_type="pil",
        )

        image = result.images[0]
        if hasattr(image, "mode"):
            image = image.convert("RGB")

        # MPS fp16 bug fallback: reject all-black frames
        import numpy as np

        if float(np.array(image).mean()) < 4.0:
            logger.warning(
                "Generated image is nearly black on %s — check MPS/float32 settings",
                self._device,
            )

        return image
