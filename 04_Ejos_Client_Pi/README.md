# Pi — Vosk STT + Piper TTS (client.py)

Bu klasör, Raspberry Pi üzerinde **offline STT (Vosk)** ve **offline TTS (Piper)** ile çalışan `client.py` istemcisi için ayrılmıştır.

## Amaç
- Raspberry Pi’de mikrofon girdisini alıp Vosk ile yazıya çevirmek (STT).
- Piper ile Türkçe TTS üretip hoparlörden vermek.
- İstenirse Pi tarafında GPIO/Arduino (Pi master / Arduino slave) ile komut/sensör kontrolüne bağlamak.

## Opsiyonel: GPIO / Arduino entegrasyonu
Bu klasör ayrıca Raspberry Pi üzerinde GPIO pinleri kullanarak sensör/aktüatör kontrolü ve Arduino ile haberleşme (Pi master / Arduino slave) senaryoları için ayrılmıştır.

- Haberleşme opsiyonları: I2C veya UART (projeye göre seçilir).
- Pi ↔ Arduino I2C kullanımında voltaj farkına dikkat edilmelidir (Pi 3.3V). Gerekiyorsa level shifter kullanın.
- Bu bölüm opsiyoneldir; temel kullanım sadece Vosk (STT) + Piper (TTS) + `client.py` üzerinedir.

## Dosyalar
- `setup.sh`  
  Pi üzerinde tüm bağımlılıkları kurar, `venv` oluşturur, Vosk TR modelini indirir, Piper binary + TR ses modelini indirir.
- `client.py`  
  STT/TTS yapan istemci uygulama.

## Kurulum (setup.sh)
1) Script’e izin ver:
```bash
chmod +x setup.sh
```


2) Çalıştır:
```bash
./setup.sh
```

Kurulum sonunda şu yollar oluşur:
- `./venv/` (Python sanal ortam)
- `../binaries/vosk/model/` (Vosk TR modeli)
- `../binaries/piper/piper` (Piper binary)
- `../binaries/piper/tr_TR-fahrettin-medium.onnx` (Piper TR ses modeli)

> Not: `pyaudio` kurulumu için `portaudio19-dev` gerekir; `setup.sh` bunu kurar.

## Çalıştırma
```bash
source venv/bin/activate
python3 client.py
```

Çıkış:

```bash
deactivate
```


## Mimari notu (ARM64 / ARMv7)
`setup.sh` Pi mimarisini `uname -m` ile algılayıp uygun Piper binary’yi indirmeye çalışır.
- 64-bit Pi OS → `arm64/aarch64`
- 32-bit Pi OS → `armv7l/armhf`

Eğer Piper indirme linki release’e göre değişirse, `setup.sh` içindeki `PIPER_BIN_URL` değişkenini override edebilirsin.

## Hızlı testler

### Vosk modeli var mı?
```bash
ls -lah ../binaries/vosk/model | head
```

### Piper çalışıyor mu?
```bash
echo "Merhaba" | ../binaries/piper/piper --model ../binaries/piper/tr_TR-fahrettin-medium.onnx --output_file /tmp/test.wav
aplay /tmp/test.wav
```