# EjOS — Local LLM + Web + Voice + Pi Client

## NOT: Bu sistemin geliştirilmesinde, yaygın modern pratiklere uygun olarak LLM destekli kodlama araçları kullanılmıştır.

EjOS; Lenovo IdeaPad Z580 üzerinde çalışan Ollama tabanlı yerel LLM altyapısını, Exper üzerinde web panel ve sesli asistan (STT→LLM→TTS) istemcilerini ve Raspberry Pi üzerinde offline STT/TTS istemcisini bir araya getiren, düşük donanım kaynaklarına sahip sistemlerde çevrimdışı sesli etkileşim için tasarlanmış, aktif olarak kullanılan, çok cihazlı bir yerel yapay zekâ sistemidir.

Status: Active / In Use
```text
[ Mic ] -> [ STT ] -> [ LLM (Ollama) ] -> [ TTS ] -> [ Speaker ]
                      |                |
                   Web UI           Pi Client
```

## Donanım (Test Ortamı)
- Exper: Exper Active DEX-144(linux Mint 21.3)
  - CPU: Intel Celeron 1037U
  - RAM: 4 GB DDR3
  - Depolama: HDD (kapasite modele göre değişebilir; örn. 500 GB varyantlar bulunur)
- Lenovo: Lenovo IdeaPad Z580 (Ubuntu Server 24.04.3)
- Raspberry Pi: 3B+

## Repo Yapısı
- `01_Lenovo-Ollama-Server/`
  - `setup-ollama.sh`: Lenovo’da Ollama + izleme araçları + model hazırlığı (senaryo 1 ve 2)
  - `Web_Chat/`: Lenovo üzerinde tek cihaz kullanım için web chat paneli (`main.py`, `index.html`)
  - `Ejos_stats/`: Exper’in kullanacağı stats server (`lenovo_stats_server.py`, `setup.sh`)
  - `Modelfile_Ejos-ai/`: Model dosyaları (örn. `Ejos_V1.gguf`, Modelfile)
  - `Readme.md`: Lenovo tarafı detay dokümantasyon

- `02_Exper-Voice-Client/VoiceAgent/`
  - `Ejos.py`: sesli asistan pipeline
  - `setup.sh`, `Start.sh`, `Stop.sh`
  - `Readme.md`

- `03_Exper-Web-Client/`
  - `main.py`, `index.html`, `script.js`, `style.css`, `setup.sh`
  - `Readme.md`

- `04_Ejos_Client_Pi/`
  - `clientpi.py`: Vosk STT + Piper TTS client
  - `Setup.sh`
  - `Readme.md`

- `05_Ejos_Models/`
  - Dataset toplama → birleştirme → EN→TR çeviri → LoRA eğitim → GGUF export pipeline’ı.
  - Detay: `05_Ejos_Models/README.md`


## Ağ Topolojisi (Lab Network)
Lenovo (Z580), Exper Active Dex 144 ve Raspberry Pi; eski bir modem cihazı switch gibi kullanılarak aynı yerel ağa bağlanmıştır.
Cihazlar aynı subnet üzerinde IP alarak (DHCP veya statik) birbirleriyle haberleşir.

> Not: Ağda IP dağıtımını tek bir DHCP sunucusu yapmalıdır; eski modem “switch” gibi kullanılacaksa genellikle DHCP kapatılır ve LAN-LAN bağlanır.


## Hızlı Başlangıç (3 Senaryo)

### Senaryo 1 — Tek cihaz (Lenovo: Ollama + Web Chat)
1) Lenovo’da kurulum:
```bash
cd 01_Lenovo-Ollama-Server
chmod +x setup-ollama.sh
./setup-ollama.sh
```

2) Web chat:
```bash
cd Web_Chat
python3 main.py
```
3) Tarayıcıdan:
- `http://LENOVO_IP:8000/`

### Senaryo 2 — 2 cihaz (Exper Web Panel, Lenovo Servis)
1) Lenovo: Ollama kurulumu (yukarıdaki `setup-ollama.sh`)
2) Lenovo: stats server:
```bash
cd 01_Lenovo-Ollama-Server/Ejos_stats
chmod +x setup.sh
./setup.sh
```
3) Exper: web panel:
```bash
cd 03_Exper-Web-Client
chmod +x setup.sh
./setup.sh
python3 main.py
```

### Senaryo 3 — Raspberry Pi istemci (Offline STT/TTS)
```bash
cd 04_Ejos_Client_Pi
chmod +x Setup.sh
./Setup.sh
source venv/bin/activate
python3 clientpi.py
```

## Notlar
- IP öğrenmek için: `ip a`
- Her `.sh` dosyasını çalıştırmadan önce: `chmod +x dosya.sh`
- Detay kurulum/konfigürasyon için her klasörün içindeki `Readme.md` dosyasına bak.
- Her klasördeki setup.sh / Setup.sh isimleri büyük-küçük harfe duyarlıdır (Linux).

## ⚖️ License & Trademark Notice

### Software License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.
- You may use, copy, modify, and distribute this software under the terms of GPL-3.0.
- If you distribute modified versions or derivative works, you must provide the corresponding source code under GPL-3.0.

### Trademark Notice
**"EjOS"** and the **EjOS logo** are trademarks of **Bünyamin Öksüz**.
- For trademark usage details, see TRADEMARK.md.

- Third parties are **not permitted** to use the **"EjOS"** name or the **EjOS logo** to publish, market, brand, or redistribute any software, fork, derivative, service, or product.
- You may **not** release modified versions or forks under the name **"EjOS"** or any confusingly similar name (e.g., "EjOS AI", "EjOS OS").
- If you redistribute a **modified version or a fork**, you must **remove EjOS branding** (name/logo) and use your **own** name and branding.
- This trademark restriction does not limit the rights granted by GPL-3.0 to the source code; it only restricts use of the **name and logo**.
