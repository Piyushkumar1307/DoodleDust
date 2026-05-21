#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install torch torchvision
pip install -r requirements.txt
pip install -U peft

echo ""
echo "PEFT check:"
python -c "import peft; from diffusers.utils import USE_PEFT_BACKEND; print('peft', peft.__version__, '| USE_PEFT_BACKEND', USE_PEFT_BACKEND)"
echo ""
echo "Start server:"
echo "  cd backend && source .venv/bin/activate && python app.py"
