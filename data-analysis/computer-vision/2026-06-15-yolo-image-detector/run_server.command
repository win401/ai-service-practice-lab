#!/bin/bash
cd "$(dirname "$0")/app"

if [ ! -d ".venv" ]; then
  echo "가상환경 생성 중..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt -q
python app.py
