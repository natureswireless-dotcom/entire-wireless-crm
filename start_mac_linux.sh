#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt
export DATA_DIR="${DATA_DIR:-$PWD/data}"
export SECRET_KEY="${SECRET_KEY:-local-dev-secret-change-me}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin@natureswireless.org}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-ChangeMe123!}"
uvicorn main:app --host 127.0.0.1 --port 8000
