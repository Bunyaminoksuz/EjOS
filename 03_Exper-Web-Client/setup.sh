#!/usr/bin/env bash
set -e

BASE_DIR="$HOME/EjOS"
PANEL_DIR="$BASE_DIR/EjOS_panel"
VENV_DIR="$PANEL_DIR/venv"

echo "[1/7] Panel klasörü hazırlanıyor: $PANEL_DIR"
mkdir -p "$PANEL_DIR"

echo "[2/7] venv kurulumu"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

echo "[3/7] venv aktif"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[4/7] pip güncelle"
python -m pip install --upgrade pip setuptools wheel

echo "[5/7] paketleri kur"
pip install fastapi uvicorn requests pydantic

echo "[6/7] chats.json hazırla"
cd "$PANEL_DIR"
if [ ! -f chats.json ]; then
  echo "[]" > chats.json
fi

echo "[7/7] bitti"
echo "Çalıştırma:"
echo "  cd $PANEL_DIR"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Not: main.py dosyanı $PANEL_DIR/main.py olarak koy."
