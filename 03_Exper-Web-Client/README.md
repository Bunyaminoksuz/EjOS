## Web Client (EjOS Panel)

EjOS Panel, Exper üzerinde çalışan web arayüzüdür ve Lenovo’daki iki servisi tek noktadan kullanır:
- Ollama chat API (LLM cevapları).
- Lenovo sistem istatistikleri (`/stats`).

### Mimari

- Exper (panel backend + frontend)
  - FastAPI backend: `~/EjOS/EjOS_panel/main.py`
  - API uygulaması `/api` altında mount edilir (çakışmayı önlemek için ayrı FastAPI instance).
  - Static web panel: aynı klasördeki `index.html` (ve varsa `js/css`) `StaticFiles` ile root `/` altında servis edilir.
  - Chat geçmişi: `~/EjOS/EjOS_panel/chats.json` dosyasına yazılır/okunur.

- Lenovo (servisler)
  - Ollama: `http://LENOVO_HOST:11434/api/chat`
  - Stats server: `http://LENOVO_HOST:9000/stats` (`lenovo_stats_server.py`)

### Panelin yaptığı işler (özellikler)

- Web arayüz servis etme
  - `GET /` → panel arayüzü (static)

- Model ile sohbet
  - `POST /api/chat` → mesajı Lenovo’daki Ollama’ya iletir ve cevabı stream olarak geri verir (`StreamingResponse`)

- Sistem istatistikleri
  - `GET /api/stats` → Lenovo’daki `/stats` endpoint’ini çağırır ve JSON döndürür
  - Lenovo’ya ulaşılamazsa:
    - `502`: upstream/bağlantı hatası
    - `504`: timeout

- Chat geçmişi yönetimi
  - `GET /api/history` → `chats.json` içeriğini döndürür
  - `POST /api/save_chat` → sohbeti kaydeder/günceller (en üste taşır)
  - `POST /api/delete_chat` → sohbeti siler

### Endpoint’ler
- `GET /api/history`
- `POST /api/save_chat`
- `POST /api/delete_chat`
- `POST /api/chat` (StreamingResponse)
- `GET /api/stats`
- `GET /api/docs` (FastAPI Swagger UI)

### Çalıştırma (Exper)

1) Klasöre gir ve venv’i aç:
```bash
cd ~/EjOS/EjOS_panel
source venv/bin/activate
```

2) Lenovo hedefini ayarla (opsiyonel ama önerilir):
```bash
export LENOVO_HOST="192.168.55.1"
export LENOVO_OLLAMA_PORT="11434"
export LENOVO_STATS_PORT="9000"
```

3) Çalıştır:
```bash
python3 main.py
```
4) Erişim:
- Panel: `http://EXPER_IP:8000/`
- API docs: `http://EXPER_IP:8000/api/docs`
