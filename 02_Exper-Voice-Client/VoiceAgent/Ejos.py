import os, time, subprocess, requests, json, re, threading, queue

# ========== CONFIG ==========
OLLAMA_URL = "http://192.168.55.1:11434/api/generate"
OLLAMA_MODEL = "ejos-ai"

WHISPER_BIN   = "/home/ejos/EjOS/Voice/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "/home/ejos/EjOS/Voice/whisper.cpp/models/ggml-tiny.bin"  # sende var: 466M

# VAD (sende kullanmıştın)
VAD_MODEL = "/home/ejos/EjOS/Voice/whisper.cpp/models/for-tests-silero-v6.2.0-ggml.bin"
USE_VAD = True
VAD_THRESHOLD = "0.35"

# “EjOS” ve sık kelimeler için ipucu
WHISPER_PROMPT = (
    "Konuşma dili Türkçe. Asistanın adı EjOS. "
    "Sık kelimeler: günaydın, selam, nasılsın, kuantum, parasetamol."
)

PIPER_BIN   = "/home/ejos/EjOS/Voice/Piper/piper/piper"
PIPER_MODEL = "/home/ejos/EjOS/Voice/Piper/tr_TR-fahrettin-medium.onnx"

# Playback: sende çalıştı
APLAY_DEV = "pulse"

TMP_WAV  = "/tmp/ejos_in.wav"
OUT_BASE = "/tmp/ejos_out"
OUT_TXT  = OUT_BASE + ".txt"
TMP_TTS  = "/tmp/ejos_tts.wav"

# Daha doğru için daha uzun chunk (cümleyi bölmesin)
CHUNK_SEC = 8
WHISPER_TIMEOUT = 180   # small model + CPU için daha geniş

SENTENCES_PER_TTS = 2

def run(cmd, timeout=None, input_text=None):
    return subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=timeout)

def record_chunk(sec: int) -> bool:
    if os.path.exists(TMP_WAV):
        os.remove(TMP_WAV)
    
    cmd = [
        "bash", "-lc",
        f"timeout {sec+1}s "
        f"parec --format=s16le --rate=16000 --channels=1 | "
        f"sox -t raw -r 16000 -c 1 -e signed-integer -b 16 - {TMP_WAV} gain -n"
    ]
    r = run(cmd, timeout=sec + 8)
    if r.returncode != 0 and r.stderr:
        print("[record err]", r.stderr.strip()[:200])

    return os.path.exists(TMP_WAV) and os.path.getsize(TMP_WAV) > 1000

def whisper_txt(wav_path: str) -> str:
    if os.path.exists(OUT_TXT):
        try: os.remove(OUT_TXT)
        except: pass

    cmd = [
        WHISPER_BIN,
        "--no-gpu",
        "--language", "tr",
        "--prompt", WHISPER_PROMPT,
        "--carry-initial-prompt",
        "-m", WHISPER_MODEL,
        "-f", wav_path,
        "-nt",
        "-otxt",
        "-of", OUT_BASE,
        "--suppress-nst",
    ]

    if USE_VAD:
        cmd += ["--vad", "--vad-model", VAD_MODEL, "--vad-threshold", VAD_THRESHOLD]

    try:
        r = run(cmd, timeout=WHISPER_TIMEOUT)
        if r.returncode != 0 and r.stderr:
            print("[whisper err]", r.stderr.strip()[:250])
    except subprocess.TimeoutExpired:
        print("[whisper] TIMEOUT")
        return ""

    if not os.path.exists(OUT_TXT):
        return ""

    return open(OUT_TXT, "r", encoding="utf-8", errors="ignore").read().strip()

def split_into_sentences(text: str):
    parts = re.split(r'(?<=[.!?])\s+', (text or "").strip())
    return [p.strip() for p in parts if p.strip()]

# TTS
tts_queue = queue.Queue()

def tts_worker():
    while True:
        item = tts_queue.get()
        if item is None:
            break

        text = item.strip()
        if not text:
            tts_queue.task_done()
            continue

        p = run(
            [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", TMP_TTS],
            timeout=180,
            input_text=text + "\n"
        )
        if p.returncode != 0:
            print("[piper err]", (p.stderr or "")[:400])
            tts_queue.task_done()
            continue

        if not os.path.exists(TMP_TTS) or os.path.getsize(TMP_TTS) < 1000:
            print("[tts] WAV oluşmadı/boş")
            tts_queue.task_done()
            continue

        subprocess.run(
            ["aplay", "-D", APLAY_DEV, TMP_TTS],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )

        tts_queue.task_done()

threading.Thread(target=tts_worker, daemon=True).start()

# OLLAMA
def ask_ollama_stream_tts(prompt: str):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
    carry = ""
    buffer = ""

    with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600) as r:
        r.raise_for_status()

        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            part = data.get("response") or ""
            if part:
                print(part, end="", flush=True)
                buffer += part

                all_text = (carry + buffer).strip()
                sents = split_into_sentences(all_text)

                ends_with_terminal = bool(re.search(r'[.!?]\s*$', all_text))
                if not ends_with_terminal and sents:
                    carry = sents.pop()
                else:
                    carry = ""

                while len(sents) >= SENTENCES_PER_TTS:
                    pack = " ".join(sents[:SENTENCES_PER_TTS])
                    sents = sents[SENTENCES_PER_TTS:]
                    tts_queue.put(pack)

                if sents:
                    carry = ((" ".join(sents)) + (" " + carry if carry else "")).strip()

                buffer = ""

            if data.get("done") is True:
                break

    final_text = (carry + " " + buffer).strip()
    if final_text:
        tts_queue.put(final_text)

print("EjOS FINAL: 8 sn kayıt + Whisper small(VAD+prompt) + Ollama stream + 2 cümlede konuşma. Çıkış: Ctrl+C")

try:
    while True:
        if not record_chunk(CHUNK_SEC):
            time.sleep(0.1)
            continue

        user_text = whisper_txt(TMP_WAV)
        if not user_text:
            continue

        print("\nKullanıcı:", user_text)
        print("EjOS:", end=" ", flush=True)

        try:
            ask_ollama_stream_tts(user_text)
        except Exception as e:
            print("\nOllama hata:", e)
            tts_queue.put("Bağlantı hatası oluştu.")

        print("\n")  

except KeyboardInterrupt:
    pass
finally:
    tts_queue.put(None)
