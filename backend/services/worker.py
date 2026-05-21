from typing import Any, Dict

import numpy as np

from config import settings
from services.image_utils import (
    decode_sketch,
    image_to_data_url,
    prepare_control_sketch,
    resize_cover,
)
from services.pipeline import GenerationPipeline, DEFAULT_NEGATIVE
from services.queue import Job


def process_job(job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
    if job.cancel_event.is_set():
        return {}

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("prompt is required")

    sketch = decode_sketch(payload["sketch"])
    live_w = settings.live_width
    live_h = settings.live_height
    sketch_sized = resize_cover(sketch, live_w, live_h)
    control_image = prepare_control_sketch(sketch_sized)

    if job.cancel_event.is_set():
        return {}

    pipe = GenerationPipeline.get()
    seed = payload.get("seed")
    if seed is not None:
        seed = int(seed)

    full_prompt = (
        f"{prompt}, same composition and layout as the sketch, "
        "preserve every drawn line, river, path, and shape from the drawing"
    )

    image = pipe.generate(
        control_image,
        full_prompt,
        profile="live",
        negative_prompt=payload.get("negative_prompt") or DEFAULT_NEGATIVE,
        seed=seed,
        steps=payload.get("steps"),
        guidance_scale=payload.get("guidance_scale"),
        controlnet_scale=payload.get("controlnet_scale"),
        width=live_w,
        height=live_h,
    )

    if job.cancel_event.is_set():
        return {}

    if float(np.array(image).mean()) < 4.0:
        raise RuntimeError(
            "Model returned a black image. Restart backend and try again."
        )

    return {
        "image": image_to_data_url(image),
        "seed": seed,
        "device": pipe.device,
    }
