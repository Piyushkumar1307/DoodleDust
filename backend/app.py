import logging
import os
import threading

# Avoid MPS ops failing silently on Mac (helps prevent black/blank outputs)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

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
    threading.Thread(target=_warmup_models, daemon=True).start()
    app = create_app()
    logger.info("Starting on http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=False, threaded=True)
