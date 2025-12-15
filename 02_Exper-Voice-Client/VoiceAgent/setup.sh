#!/usr/bin/env bash
# MUTLAKA CHMOD YAPINIZZ!!!!!!!
set -e

BASE="$HOME/EjOS"
VOICE_DIR="$BASE/Voice"
APP_DIR="$BASE/ejos_voice"
VENV="$APP_DIR/venv"

WHISPER_REPO="$VOICE_DIR/whisper.cpp"
WHISPER_BIN="$WHISPER_REPO/build/bin/whisper-cli"

PIPER_BIN="$VOICE_DIR/Piper/piper/piper"

# tiny model (sen "tiny olmalı" dedin)
WHISPER_MODEL="$WHISPER_REPO/models/ggml-tiny.bin"

# sende vardı (VAD ggml)
VAD_MODEL="$WHISPER_REPO/models/for-tests-silero-v6.2.0-ggml.bin"

echo "[1/8] Sistem paketleri (parec/sox/aplay)..."
sudo apt-get update -y
sudo apt-get install -y pulseaudio-utils sox alsa-utils

echo "[2/8] Uygulama klasörü..."
mkdir -p "$APP_DIR"

echo "[3/8] Python venv..."
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "[4/8] Python paketleri..."
python -m pip install --upgrade pip setuptools wheel
pip install requests

echo "[5/8] Dosya kontrolleri..."
if [ ! -x "$WHISPER_BIN" ]; then
  echo "HATA: whisper-cli yok veya çalıştırılabilir değil: $WHISPER_BIN"
  echo "whisper.cpp build etmen gerekiyor (build klasörün eksik olabilir)."
  exit 1
fi

if [ ! -x "$PIPER_BIN" ]; then
  echo "HATA: piper binary yok: $PIPER_BIN"
  exit 1
fi

echo "[6/8] Whisper tiny model kontrol..."
if [ ! -f "$WHISPER_MODEL" ]; then
  echo "Uyarı: tiny model bulunamadı: $WHISPER_MODEL"
  if [ -f "$WHISPER_REPO/models/download-ggml-model.sh" ]; then
    echo "İndirmeyi deniyorum: ggml-tiny.bin"
    bash "$WHISPER_REPO/models/download-ggml-model.sh" tiny || true
  fi
fi

echo "[7/8] VAD model kontrol..."
if [ ! -f "$VAD_MODEL" ]; then
  echo "Uyarı: VAD modeli bulunamadı: $VAD_MODEL"
  echo "VAD olmadan da çalışır ama USE_VAD=True ise hata alırsın."
fi

echo "[8/8] Bitti."
echo ""
echo "Şimdi python scriptini $APP_DIR/ejos_voice.py olarak koy."
echo "Çalıştırma:"
echo "  cd $APP_DIR"
echo "  source venv/bin/activate"
echo "  python3 ejos_voice.py"
echo ""
echo "Not: ejos_voice.py içinde WHISPER_MODEL şunu göstermeli:"
echo "  $WHISPER_MODEL"
