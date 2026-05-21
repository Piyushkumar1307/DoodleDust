import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5001"))
    preview_width: int = int(os.getenv("PREVIEW_WIDTH", "512"))
    preview_height: int = int(os.getenv("PREVIEW_HEIGHT", "512"))
    inference_steps: int = int(os.getenv("INFERENCE_STEPS", "8"))
    guidance_scale: float = float(os.getenv("GUIDANCE_SCALE", "5.5"))
    controlnet_scale: float = float(
        os.getenv("CONTROLNET_CONDITIONING_SCALE", "1.0")
    )
    # Fast path for Doodle Dust AI (LCM)
    live_width: int = int(os.getenv("LIVE_WIDTH", "384"))
    live_height: int = int(os.getenv("LIVE_HEIGHT", "384"))
    live_steps: int = int(os.getenv("LIVE_STEPS", "4"))
    live_guidance_scale: float = float(os.getenv("LIVE_GUIDANCE_SCALE", "1.8"))
    live_controlnet_scale: float = float(
        os.getenv("LIVE_CONTROLNET_CONDITIONING_SCALE", "0.9")
    )
    lcm_lora_id: str = os.getenv(
        "LCM_LORA_ID", "latent-consistency/lcm-lora-sdv1-5"
    )
    sd_model_id: str = os.getenv("SD_MODEL_ID", "runwayml/stable-diffusion-v1-5")
    controlnet_model_id: str = os.getenv(
        "CONTROLNET_MODEL_ID", "lllyasviel/control_v11p_sd15_scribble"
    )
    max_queue_size: int = int(os.getenv("MAX_QUEUE_SIZE", "8"))
    generation_timeout_sec: int = int(os.getenv("GENERATION_TIMEOUT_SEC", "120"))


settings = Settings()
