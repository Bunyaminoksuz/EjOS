# README.md — EjOS Voice (Exper)

## Amaç
Bu modül Exper cihazında “konuşan EjOS” pipeline’ını çalıştırır:

- Mikrofon kaydı (PulseAudio `parec` + `sox`)
- STT: `whisper.cpp` (`ggml-tiny.bin` + Türkçe prompt + opsiyonel VAD)
- LLM: Lenovo’daki Ollama’ya istek (`/api/generate`, stream)
- TTS: Piper (`tr_TR-fahrettin-medium.onnx`)
- Ses çıkışı: `aplay` (PulseAudio device)

## Klasör Yapısı
Önerilen konumlar:

- Uygulama: `~/EjOS/ejos_voice/`
  - `ejos_voice.py` (ana python dosyası)
  - `venv/` (python sanal ortam)
  - `voice.log` (start script ile log)
  - `voice.pid` (start script ile PID)

- Bağımlılıklar:
  - `~/EjOS/Voice/whisper.cpp/` (build edilmiş repo)
  - `~/EjOS/Voice/Piper/` (piper binary + model)

## Gereksinimler

### Sistem paketleri
- `pulseaudio-utils` (parec)
- `sox`
- `alsa-utils` (aplay)

### Whisper.cpp
- Binary: `~/EjOS/Voice/whisper.cpp/build/bin/whisper-cli`
- Model: `~/EjOS/Voice/whisper.cpp/models/ggml-tiny.bin`
- (Opsiyonel) VAD: `~/EjOS/Voice/whisper.cpp/models/for-tests-silero-v6.2.0-ggml.bin`

> Tiny model yoksa (whisper.cpp repo içinde), indir:
cd ~/EjOS/Voice/whisper.cpp/models
bash ./download-ggml-model.sh tiny

Bu script `models/ggml-tiny.bin` dosyasını indirir.
### Piper
- Binary: `~/EjOS/Voice/Piper/piper/piper`
- Model: `~/EjOS/Voice/Piper/tr_TR-fahrettin-medium.onnx`

### Ağ
- Lenovo Ollama: `http://192.168.55.1:11434/api/generate` (gerekirse IP değişebilir)

## ejos_voice.py Konfig
Python dosyasında kritik ayarlar:

- `OLLAMA_URL = "http://192.168.55.1:11434/api/generate"`
- `OLLAMA_MODEL = "ejos-ai"`
- `WHISPER_MODEL = "/home/ejos/EjOS/Voice/whisper.cpp/models/ggml-tiny.bin"`
- `USE_VAD = True` ve `VAD_THRESHOLD = "0.35"`
- `CHUNK_SEC = 8` (8 saniyelik kayıt parçaları)
- `SENTENCES_PER_TTS = 2` (2 cümlede bir konuşma)

## Kurulum (setup.sh)
1) Yetki ver:
chmod +x ~/EjOS/setup_voice.sh

2) Çalıştır:
~/EjOS/setup_voice.sh


Kurulumdan sonra `ejos_voice.py` dosyasını şuraya koy:
- `~/EjOS/ejos_voice/ejos_voice.py`

## Çalıştırma (manuel)
cd ~/EjOS/ejos_voice
source venv/bin/activate
python3 ejos_voice.py


Çıkış: `Ctrl+C`

## Çalıştırma (start/stop script ile)
Başlat:
chmod +x ~/EjOS/start_voice.sh
~/EjOS/start_voice.sh
tail -f ~/EjOS/ejos_voice/voice.log

Durdur:
chmod +x ~/EjOS/stop_voice.sh
~/EjOS/stop_voice.sh


## Hızlı Testler

### Mikrofon kaydı geliyor mu?
parec --list-sources | head


### Lenovo Ollama erişimi var mı? (Exper’den)
curl -s "http://192.168.55.1:11434/api/tags" | head



### Piper çalışıyor mu?
echo "Merhaba" | ~/EjOS/Voice/Piper/piper/piper --model ~/EjOS/Voice/Piper/tr_TR-fahrettin-medium.onnx --output_file /tmp/test.wav
aplay -D pulse /tmp/test.wav