## Lenovo (Lenovo IdeaPad Z580) — Ollama + Panel + Stats

Bu dizin Lenovo IdeaPad Z580 (Ubuntu Server 24.04.3) üzerinde EjOS’un çalışması için gerekli kurulumları ve kullanım senaryolarını içerir.

### Bu makine ne yapıyor?
- Ollama üzerinde `ejosv1` (GGUF) modeli çalıştırır ve chat API sağlar.
- Sistem istatistiklerini (CPU/RAM/sıcaklık) üretir.
- İsteğe bağlı olarak web paneli **direkt Lenovo üzerinde** çalıştırıp (tek cihaz senaryosu) tarayıcıdan sohbet edebilirsin.
- Alternatif olarak Exper web paneli Lenovo’nun servislerini uzaktan kullanabilir.

### Servisler / Portlar
- Ollama API: `http://LENOVO_IP:11434/api/chat`
- Lenovo stats (Senaryo 2): `http://LENOVO_IP:9000/stats`
- Web Panel (Senaryo 1): `http://LENOVO_IP:8000/`

> IP öğrenmek için: `ip a`

---

## Senaryo 1 — Tek cihaz (Lenovo local panel)
Bu senaryoda panel de Lenovo’da çalışır ve Ollama’ya localhost üzerinden bağlanır (`127.0.0.1:11434`).

### Kurulum
Bu senaryoda **setup-ollama.sh** yeterlidir.

#### setup-ollama.sh ne yapar?
- `apt update/upgrade` yapar.
- İzleme araçlarını kurar: `htop`, `lm-sensors`.
- `sensors-detect --auto` çalıştırıp sensörleri hazırlar.
- Ollama’yı kurar (resmi install script ile).
- Temel modeli indirir (örn. `llama3:8b`) ve varsa `Modelfile` ile özel model oluşturur.
- Ollama servisini restart eder.

### Çalıştırma (Panel)
Panel dizinine geçip:
```bash
python3 main.py
``` 

### Erişim
- Panel: `http://LENOVO_IP:8000/`
- Panel API docs (tek app ise): `http://LENOVO_IP:8000/docs`

---

## Senaryo 2 — 2 cihaz (Exper panel, Lenovo servis)
Bu senaryoda Lenovo sadece “servis sağlayıcı”dır:
- Exper panel → Lenovo Ollama API
- Exper panel → Lenovo stats server

### Kurulum
Bu senaryoda iki şey kurulur:
1) **setup-ollama.sh** (Ollama + model)
2) **setup_lenovo_stats.sh** (stats server)

#### setup_lenovo_stats.sh kullanımı
Setup yaptıktan sonra mutlaka çalıştırılabilir yap:

```bash
chmod +x setup_lenovo_stats.sh
```
Kurulumu başlat:

```bash
./setup_lenovo_stats.sh
```


Bu script ne yapar?
- `python3-venv`, `python3-full`, `lm-sensors` kurar.
- `$HOME/ejos-stats` altında venv oluşturur (`python3 -m venv ...`).
- `fastapi uvicorn psutil` paketlerini venv içine kurar.
- `lenovo_stats_server.py` dosyasını otomatik yazar.

#### Stats server çalıştırma
```bash
cd $HOME/ejos-stats
$HOME/ejos-stats/venv/bin/uvicorn lenovo_stats_server:app --host 0.0.0.0 --port 9000
```

Test:
```bash
curl -s "http://127.0.0.1:9000/stats"
```

> `--host 0.0.0.0` LAN’dan erişim için kullanılır.

---

## Senaryo 3 — Raspberry Pi istemci
Exper kullanılmıyorsa Raspberry Pi sadece istemci (tarayıcı) olarak Lenovo paneline bağlanabilir:
- `http://LENOVO_IP:8000/`

Senaryo 3’ü kullanmak istiyorsanız `ejos_client_pi/Setup.sh` script’ini Raspberry Pi üzerinde kurmanız gerekir.

> Not: Her `.sh` dosyasını çalıştırmadan önce `chmod +x dosya.sh` yapın.
