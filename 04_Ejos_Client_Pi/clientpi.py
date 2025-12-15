import os
import sys
import json
import requests
import subprocess
import pyaudio
from vosk import Model, KaldiRecognizer
import time

# --- AYARLAR (KABLOLU AĞ) ---
# Laptop'un (Ubuntu Server) gelecekteki IP adresi
SERVER_URL = "http://192.168.55.1:8000/api/chat"

# Dosya yolları
PIPER_EXECUTABLE = "./piper/piper"
VOICE_MODEL = "tr_TR-fahrettin-medium.onnx"
VOSK_MODEL_PATH = "model"

# --- KONTROLLER ---
if not os.path.exists(VOSK_MODEL_PATH):
    print("HATA: 'model' klasörü yok! Lütfen indirmeleri kontrol et.")
    sys.exit(1)

print(">> Sistem Başlatılıyor... (Model yükleniyor)")
# Vosk modelini yükle
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()

def konus_offline(metin):
    """Piper TTS kullanarak metni okur"""
    if not metin: return
    print(f"EjOS: {metin}")
    
    # Matematik sembollerini temizle ki 'dolar işareti' diye okumasın
    temiz = metin.replace("*", "").replace("$", "").replace("#", "").replace("_", " ")
    
    # Piper komutu
    komut = f'echo "{temiz}" | {PIPER_EXECUTABLE} --model {VOICE_MODEL} --output-raw | aplay -r 22050 -f S16_LE -t raw -q'
    
    try:
        subprocess.run(komut, shell=True, executable='/bin/bash')
    except Exception as e:
        print(f"Ses Hatası: {e}")

def sunucuya_sor(soru):
    """Kablolu ağdan sunucuya sorar"""
    try:
        print(">> Sunucuya soruluyor...")
        payload = {"message": soru}
        # Timeout 5 saniye
        response = requests.post(SERVER_URL, json=payload, stream=True, timeout=5)
        
        tam_cevap = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                tam_cevap += decoded
        return tam_cevap
    except Exception as e:
        return "Sunucuya ulaşamadım. Kabloyu kontrol et."

def main():
    # Mikrofon ayarı
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    
    konus_offline("Sistem hazır. Dinliyorum.")
    
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = res.get('text', '')
            
            if text:
                print(f"Algılandı: {text}")
                
                if "kapat" in text or "sistemi durdur" in text:
                    konus_offline("Görüşmek üzere.")
                    break
                
                cevap = sunucuya_sor(text)
                konus_offline(cevap)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass