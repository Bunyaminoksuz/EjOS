#!/usr/bin/env bash
set -e

BASE="$HOME/EjOS"
APP_DIR="$BASE/ejos_voice"
VENV="$APP_DIR/venv"
LOG="$APP_DIR/voice.log"
PIDFILE="$APP_DIR/voice.pid"

# Lenovo Ollama
export OLLAMA_URL="${OLLAMA_URL:-http://192.168.55.1:11434/api/generate}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-ejos-ai}"

# Audio / paths (istersen python scriptinde ENV'den okuyacak şekilde güncelleyebilirsin)
export APLAY_DEV="${APLAY_DEV:-pulse}"

cd "$APP_DIR"

if [ ! -d "$VENV" ]; then
  echo "HATA: venv yok. Önce setup_voice.sh çalıştır: $VENV"
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

if [ ! -f "$APP_DIR/ejos_voice.py" ]; then
  echo "HATA: ejos_voice.py bulunamadı: $APP_DIR/ejos_voice.py"
  exit 1
fi

# Eğer çalışıyorsa durdur
if [ -f "$PIDFILE" ]; then
  OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Eski voice process durduruluyor (PID=$OLD_PID)..."
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
  fi
  rm -f "$PIDFILE"
fi

echo "Voice başlatılıyor... log: $LOG"
nohup python3 "$APP_DIR/ejos_voice.py" >> "$LOG" 2>&1 &

NEW_PID="$!"
echo "$NEW_PID" > "$PIDFILE"
echo "OK. PID=$NEW_PID"
echo "Log izle: tail -f $LOG"
