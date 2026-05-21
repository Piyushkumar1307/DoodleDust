#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Backend venv"
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

# PyTorch: pick ONE line for your machine (https://pytorch.org)
pip install torch torchvision
# GPU (NVIDIA CUDA 12.4 example):
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true

echo "==> Frontend"
cd "$ROOT/frontend"
npm install

echo ""
echo "Done. Run backend:  cd backend && source .venv/bin/activate && python app.py"
echo "       frontend: cd frontend && npm run dev"
