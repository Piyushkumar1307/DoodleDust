import logging
import os
import sys
import threading

# Load PEFT before diffusers so LoRA / LCM works (fixes "PEFT backend is required")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

try:
    import peft  # noqa: F401, F811
except ImportError:
    peft = None  # type: ignore

from flask import Flask
from flask_cors import CORS

from config import settings
from routes.generate import init_routes
from services.pipeline import GenerationPipeline
from services.queue import GenerationQueue
from services.worker import process_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

queue = GenerationQueue(worker_fn=process_job)


def _verify_peft() -> None:
    venv = getattr(sys, "prefix", "")
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    try:
        from diffusers.utils import USE_PEFT_BACKEND
    except Exception:
        USE_PEFT_BACKEND = False

    if peft is None:
        logger.error(
            "PEFT is NOT installed. Doodle Dust AI will fail.\n"
            "  cd backend && source .venv/bin/activate && pip install peft\n"
            "  Then restart: python app.py"
        )
        return

    if not USE_PEFT_BACKEND:
        logger.warning(
            "PEFT installed but diffusers PEFT backend is off — "
            "upgrade: pip install -U peft transformers diffusers"
        )
    else:
        logger.info(
            "PEFT ready for Doodle Dust AI (venv=%s)",
            "yes" if in_venv else "no — use: source .venv/bin/activate",
        )


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    bp = init_routes(queue)
    app.register_blueprint(bp)

    @app.route("/")
    def index():
        return {
            "app": "Doodle Dust API",
            "docs": "POST /api/generate, GET /api/generate/<job_id>",
        }

    return app


def _warmup_models():
    try:
        GenerationPipeline.get().load()
    except Exception:
        logger.exception("Model warmup failed — will retry on first generation")


if __name__ == "__main__":
    _verify_peft()
    threading.Thread(target=_warmup_models, daemon=True).start()
    app = create_app()
    logger.info("Starting on http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=False, threaded=True)
