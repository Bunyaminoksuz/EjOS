#!/bin/bash
# Dosya: setup_pi_vosk.sh
# Açıklama: Raspberry Pi (ARMv7/ARMv8 mimarisi) üzerinde VOSK (STT) ve PIPER (TTS) tabanlı istemci için kurulum scripti.
# ÇALIŞTIRMADAN ÖNCE MUTLAKA CHMOD YAPIMIZ!! chmod +x setup.sh
# --- 1. AYARLAR ---
VOSK_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip"
VOSK_DIR="../binaries/vosk"
PIPER_DIR="../binaries/piper"
# Pi için en uygun mimariyi seçiyoruz (Genellikle armhf veya aarch64/arm64)
# Varsayılan olarak 64-bit Pi'ler için arm64'ü hedefleyelim:
PIPER_BIN_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64" 
PIPER_MODEL_URL="https://github.com/rhasspy/piper/releases/download/v1.2.0/tr_TR-fahrettin-medium.onnx"


# --- 2. SİSTEM BAĞIMLILIKLARI ---
echo "--- 2/5: Temel Sistem ve Ses Bağımılıkları Kurulumu ---"
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sox libttspico-utils alsa-utils

# KRİTİK: pyaudio için gerekli olan portaudio kütüphanesi
sudo apt install -y portaudio19-dev 

# --- 3. PYTHON SANAL ORTAM KURULUMU ---
echo "--- 3/5: Python Sanal Ortam Kurulumu ---"
python3 -m venv venv
source venv/bin/activate

# Gerekli Python Kütüphaneleri
pip install numpy vosk pyaudio requests

if [ $? -ne 0 ]; then
    echo "HATA: Python kütüphane kurulumu başarısız. pyaudio genellikle derleme hatası verir."
    echo "Lütfen 'sudo apt install portaudio19-dev' komutunun çalıştığından emin olun."
    exit 1
fi

# --- 4. VOSK VE PIPER KURULUMU ---
echo "--- 4/5: VOSK ve PIPER Model Kurulumu ---"
mkdir -p "$VOSK_DIR"
mkdir -p "$PIPER_DIR"

# A. VOSK Modelini İndirme
cd "$VOSK_DIR"
if [ ! -d "model" ]; then
    echo "Vosk modelini indiriliyor..."
    wget -c "$VOSK_MODEL_URL" -O vosk-model.zip
    unzip vosk-model.zip
    mv vosk-model-small-tr-0.3 model # Python kodunda bu klasör adı bekleniyor
    rm vosk-model.zip
else
    echo "Vosk modeli zaten mevcut. Atlanıyor."
fi
cd - # Ana klasöre geri dön (VoskAgent/)

# B. PIPER TTS Kurulumu
# Piper Çalıştırılabilir Dosyasını İndirme (ARM64 Mimarisi)
if [ ! -f "$PIPER_DIR/piper" ]; then
    echo "Piper çalıştırılabilir dosyasını indiriliyor (ARM64)..."
    wget -c "$PIPER_BIN_URL" -O "$PIPER_DIR/piper"
    chmod +x "$PIPER_DIR/piper"
else
    echo "Piper çalıştırılabilir dosyası zaten mevcut. Atlanıyor."
fi

# Piper Türkçe Modelini İndirme
if [ ! -f "$PIPER_DIR/tr_TR-fahrettin-medium.onnx" ]; then
    echo "Piper Türkçe modelini indiriliyor..."
    wget -c "$PIPER_MODEL_URL" -O "$PIPER_DIR/tr_TR-fahrettin-medium.onnx"
else
    echo "Piper modeli zaten mevcut. Atlanıyor."
fi


# --- 5. SON KONTROL VE BİTİRME ---
echo "--- 5/5: Kurulum Tamamlandı ---"
echo "Kodu çalıştırmak için Pi/Exper terminalinde sırasıyla:"
echo "source venv/bin/activate"
echo "python3 vosk_agent.py"
echo "Çıkış yapmak için: 'deactivate'"