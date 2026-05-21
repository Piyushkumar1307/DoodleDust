from flask import Blueprint, jsonify, request

from services.queue import JobStatus
from services.worker import process_job

bp = Blueprint("generate", __name__, url_prefix="/api")


def init_routes(queue):
    @bp.route("/health", methods=["GET"])
    def health():
        from services.pipeline import GenerationPipeline

        try:
            import peft  # noqa: F401

            peft_installed = True
        except ImportError:
            peft_installed = False

        try:
            from diffusers.utils import USE_PEFT_BACKEND

            peft_backend = bool(USE_PEFT_BACKEND)
        except Exception:
            peft_backend = False

        pipe = GenerationPipeline.get()
        return jsonify(
            {
                "status": "ok",
                "model_loaded": pipe.is_ready,
                "device": pipe.device,
                "peft_installed": peft_installed,
                "peft_backend": peft_backend,
            }
        )

    @bp.route("/generate", methods=["POST"])
    def create_generation():
        data = request.get_json(silent=True) or {}
        if not data.get("sketch"):
            return jsonify({"error": "sketch is required"}), 400
        if not (data.get("prompt") or "").strip():
            return jsonify({"error": "prompt is required"}), 400

        job = queue.submit(data)
        return jsonify({"job_id": job.id, "status": job.status.value}), 202

    @bp.route("/generate/<job_id>", methods=["GET"])
    def get_generation(job_id: str):
        job = queue.get(job_id)
        if not job:
            return jsonify({"error": "job not found"}), 404

        body = {"job_id": job.id, "status": job.status.value}
        if job.status == JobStatus.COMPLETED and job.result:
            body["image"] = job.result.get("image")
            body["device"] = job.result.get("device")
        if job.status == JobStatus.FAILED:
            body["error"] = job.error
        return jsonify(body)

    return bp
