# LiveDrawing

Real-time AI drawing app — sketch on the left, local Stable Diffusion preview on the right. **$0 API cost**: models run on your machine (Flask + React + Hugging Face diffusers).

## Architecture

```
React (canvas)  --debounced sketch-->  Flask API  -->  Job queue (cancel stale)
                                              |
                                              v
                                    SD 1.5 + ControlNet Scribble (local GPU/CPU)
```

**Optimizations built in**

- Debounced requests (1.2s after you stop drawing)
- Cancel in-flight / queued jobs when you draw again
- Single model load (singleton pipeline)
- 512×512 previews, 12 inference steps (tune in `.env`)
- FP16 on CUDA, attention slicing + CPU offload on CPU

**Scale path (still free software)**

| Stage | Change |
|-------|--------|
| Now | In-process queue, one GPU worker |
| More users | Celery + Redis queue, multiple GPU workers behind nginx |
| Frontend | Static build on Cloudflare Pages (free) |
| Inference | Same open models; add machines with GPUs you already have |

## Requirements

| | Minimum | Recommended |
|---|---------|-------------|
| **GPU** | — | NVIDIA 8GB+ VRAM |
| **RAM** | 16GB | 16GB+ |
| **Disk** | ~6GB free | For model cache (`~/.cache/huggingface`) |
| **CPU-only** | Works | Very slow (minutes per image) |

No paid APIs. First run downloads **Stable Diffusion 1.5** + **ControlNet Scribble** from Hugging Face.

## Quick start

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Terminal 1 — backend**

```bash
cd backend
source .venv/bin/activate
python app.py
```

**Terminal 2 — frontend**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 — enter a prompt, draw, preview updates after you pause.

## Configuration

Copy `backend/.env.example` to `backend/.env`:

| Variable | Default | Notes |
|----------|---------|-------|
| `INFERENCE_STEPS` | 12 | Lower = faster, rougher |
| `PREVIEW_WIDTH/HEIGHT` | 512 | Keep at 512 for 8GB VRAM |
| `CONTROLNET_CONDITIONING_SCALE` | 0.65 | Higher = follow sketch more |
| `SD_MODEL_ID` | runwayml/stable-diffusion-v1-5 | Any SD1.5-compatible model |

## API

- `GET /api/health` — model loaded?, device (`cuda` / `cpu`)
- `POST /api/generate` — `{ "prompt", "sketch" }` (data URL) → `{ job_id }`
- `GET /api/generate/<job_id>` — poll until `completed` + `image` (JPEG data URL)

## Faster inference (optional, still free)

1. **NVIDIA GPU** + CUDA PyTorch (see [pytorch.org](https://pytorch.org)).
2. Lower `INFERENCE_STEPS` to 8 in `.env`.
3. Later: swap to an LCM/Turbo LoRA in `pipeline.py` for 4-step generations.

## Project layout

```
LiveDrawing/
├── backend/          Flask, queue, diffusers pipeline
├── frontend/         React + Vite, canvas, debounced polling
└── scripts/setup.sh
```

## Honest limits at $0

- You must supply compute (your laptop/desktop GPU).
- Cloud GPU hosting is not free; this repo is designed to run **locally** first.
- CPU mode is for testing UI only, not a good realtime experience.

## License

Code: MIT. Model weights follow their respective Hugging Face licenses (SD 1.5, ControlNet).
