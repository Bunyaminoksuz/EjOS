# 01_topla.py
# Bu script; Hugging Face datasetlerini indirir, metni temizler, basit kalite filtresi uygular
# ve tekrar eden örnekleri (hash ile) eleyerek data/Ham_Veriler klasörüne .jsonl olarak yazar.
# HF_TOKEN ortam değişkeni varsa giriş yapar (gated kaynaklar için).

import os
import re
import json
import time
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

from datasets import load_dataset
from huggingface_hub import login


# -------------------- GÖREVLER (bire bir) --------------------
GOREVLER = [
    # ===================== CORE =====================
    {"dosya": "bilim_nasa.jsonl", "kaynak": "pstroe/nasa-smd-ibm-st-v2", "kategori": "Fizik", "konu": "NASA Uzay Raporu", "limit": 30000},
    {"dosya": "tip_literatur.jsonl", "kaynak": "ccdv/pubmed-summarization", "kategori": "Tıp", "konu": "Tıbbi Makale", "limit": 30000},

    {"dosya": "muh_yazilim.jsonl", "kaynak": "sahil2801/CodeAlpaca-20k", "kategori": "Yazılım", "konu": "Kodlama", "limit": 25000},
    {"dosya": "muh_genel.jsonl", "kaynak": "TIGER-Lab/MathInstruct", "kategori": "Matematik", "konu": "Mühendislik Matematiği", "limit": 30000},

    {"dosya": "bilim_fizik.jsonl", "kaynak": "camel-ai/physics", "kategori": "Fizik", "konu": "Fizik Problemi", "limit": 20000},
    {"dosya": "bilim_kimya.jsonl", "kaynak": "camel-ai/chemistry", "kategori": "Kimya", "konu": "Kimya", "limit": 20000},
    {"dosya": "bilim_biyoloji.jsonl", "kaynak": "camel-ai/biology", "kategori": "Biyoloji", "konu": "Biyoloji", "limit": 20000},

    {"dosya": "bilim_genel_sciq.jsonl", "kaynak": "allenai/sciq", "kategori": "Fizik", "konu": "SciQ", "split": "train", "limit": 12000},

    # MMLU fizik/astro
    {"dosya": "fizik_lise.jsonl", "kaynak": "cais/mmlu", "config": "high_school_physics", "kategori": "Fizik", "konu": "MMLU", "split": "test", "limit": 15000},
    {"dosya": "fizik_uni.jsonl", "kaynak": "cais/mmlu", "config": "college_physics", "kategori": "Fizik", "konu": "MMLU", "split": "test", "limit": 15000},
    {"dosya": "fizik_kavramsal.jsonl", "kaynak": "cais/mmlu", "config": "conceptual_physics", "kategori": "Fizik", "konu": "MMLU", "split": "test", "limit": 15000},
    {"dosya": "fizik_astro.jsonl", "kaynak": "cais/mmlu", "config": "astronomy", "kategori": "Uzay", "konu": "MMLU", "split": "test", "limit": 10000},

    # İleri seviye
    {"dosya": "bilim_fizik_quantum.jsonl", "kaynak": "BoltzmannEntropy/QuantumLLMInstruct", "kategori": "Kuantum", "konu": "Quantum", "split": "train", "limit": 5000},
    {"dosya": "bilim_fizik_theorem.jsonl", "kaynak": "TIGER-Lab/TheoremQA", "kategori": "Fizik", "konu": "TheoremQA", "split": "train", "limit": 5000},

    # Sohbet + Wiki
    {"dosya": "gunluk_sohbet.jsonl", "kaynak": "HuggingFaceH4/ultrachat_200k", "kategori": "Sohbet", "konu": "Günlük Diyalog", "limit": 20000},
    {"dosya": "wikipedia_tr.jsonl", "kaynak": "Alaeddin/wikipedia-turkish", "kategori": "Genel", "konu": "Ansiklopedi", "limit": 50000},

    # ===================== EEM BLOĞU =====================
    {"dosya": "eem_elektrik_ek.jsonl", "kaynak": "burman-ai/Electrical-Engineering", "kategori": "EEM", "konu": "EE Q/A", "split": "train", "limit": 5000},
    {"dosya": "eem_stem_ek.jsonl", "kaynak": "STEM-AI-mtl/Electrical-engineering", "kategori": "EEM", "konu": "EE STEM", "split": "train", "limit": 5000},
    {"dosya": "eem_arduino_multiturn.jsonl", "kaynak": "CJJones/Multiturn_Microcontroller-Arduino-LLM-Training", "kategori": "Arduino", "konu": "Multiturn", "split": "train", "limit": 5000},
    {"dosya": "eem_dialog.jsonl", "kaynak": "CJJones/LLM_Electrical_Engineering_Educational_Synthetic_Dialog", "kategori": "EEM", "konu": "Dialog", "split": "train", "limit": 5000},
    {"dosya": "eem_chat.jsonl", "kaynak": "CJJones/Electrical_Engineering_Chat", "kategori": "EEM", "konu": "Chat", "split": "train", "limit": 5000},

    # MMLU electrical engineering
    {"dosya": "eem_akademik.jsonl", "kaynak": "cais/mmlu", "config": "electrical_engineering", "kategori": "EEM", "konu": "MMLU", "split": "test", "limit": 5000},

    # MetaMath / arxiv engineering abstracts
    {"dosya": "eem_matematik.jsonl", "kaynak": "meta-math/MetaMathQA", "kategori": "Matematik", "konu": "MetaMathQA", "split": "train", "limit": 30000},
    {"dosya": "eem_makaleler.jsonl", "kaynak": "artifact-ai/arxiv-engineering-abstracts-2023", "kategori": "EEM", "konu": "ArXiv abstracts", "split": "train", "limit": 25000},

    # Verilog/code
    {"dosya": "eem_verilog.jsonl", "kaynak": "shailja/Verilog_Gemma", "kategori": "EEM", "konu": "Verilog", "split": "train", "limit": 20000},
    {"dosya": "eem_gomulu.jsonl", "kaynak": "theblackcat102/evol-codealpaca-v1", "kategori": "Yazılım", "konu": "Embedded/Code", "split": "train", "limit": 25000},
]


# -------------------- AYARLAR --------------------
OUT_DIR = os.getenv("OUT_DIR", os.path.join(os.getcwd(), "data", "Ham_Veriler"))
WORKERS = int(os.getenv("WORKERS", "2"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000"))
SLEEP_EVERY_N = int(os.getenv("SLEEP_EVERY_N", "2500"))
SLEEP_SECS = float(os.getenv("SLEEP_SECS", "0.15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

random.seed(42)


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def maybe_hf_login() -> None:
    """HF_TOKEN varsa login olur; yoksa sessizce devam eder."""
    token = os.getenv("HF_TOKEN", "").strip()
    if token:
        login(token=token)
    else:
        print("ℹ️ HF_TOKEN env yok; bazı gated datasetler indirilemeyebilir.")


def metni_temizle(text: str) -> str:
    """HTML/URL/boşluk temizliği."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def kalite_kontrolu(text: str, kategori: str) -> bool:
    """Basit kalite filtresi (özellikle wiki/ansiklopedi için biraz daha sıkı)."""
    if not text or len(text) < 30:
        return False
    if re.search(r"(.)\1{10,}", text):
        return False
    if len(text.split()) < 5:
        return False

    if kategori == "Genel":
        if len(text) < 256:
            return False
        if text.strip().startswith(("*", "#", "|", "==", "{{", "{|")):
            return False
        blocked = [
            "anlam ayrımı", "disambiguation", "may refer to",
            "liste:", "list of", "kategori:", "category:",
            "şablon:", "template:", "taslak", "stub",
        ]
        low = text.lower()
        if any(k in low for k in blocked):
            return False
        if text.count("\n") > len(text) / 50:
            return False

    max_digit_ratio = 0.7 if kategori in ["Fizik", "Kimya", "Yazılım", "Matematik"] else 0.5
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    if digit_ratio > max_digit_ratio:
        return False

    return True


def text_hash(text: str) -> str:
    """Dedupe için hash."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_dynamic_instruction(kategori: str, text: str) -> str:
    """Metnin tipine göre instruction üret (Soru/Kod/Sohbet/Genel)."""
    low = text.lower()
    if "?" in text or any(low.startswith(x) for x in ["nedir", "nasıl", "neden"]):
        return f"Sen {kategori} alanında uzman bir asistansın. Aşağıdaki soruyu detaylı yanıtla."
    if any(k in text for k in ["def ", "import ", "class "]):
        return "Sen deneyimli bir yazılım mühendisisin. Aşağıdaki kodu açıkla."
    if kategori == "Sohbet":
        return "Sen yardımsever ve doğal konuşan bir asistansın. Aşağıdaki mesaja uygun cevap ver."
    return f"Sen {kategori} konusunda uzman birisin. Aşağıdaki konuyu açıkla."


def parse_row_content(row: dict) -> str:
    """Farklı dataset şemalarını tek bir text'e indirger."""
    if isinstance(row, str):
        return row
    if "text" in row:
        return row["text"]

    if "instruction" in row and "output" in row:
        inp = row.get("input", "")
        if inp:
            return f"Soru: {row['instruction']}\nGirdi: {inp}\nCevap: {row['output']}"
        return f"Soru: {row['instruction']}\nCevap: {row['output']}"

    if "question" in row and "answer" in row:
        return f"Soru: {row['question']}\nCevap: {row['answer']}"

    # MMLU tarzı (question + choices + answer index/harf)
    if "question" in row and "choices" in row:
        q = row.get("question", "")
        choices = row.get("choices", [])
        ans = row.get("answer", 0)
        if isinstance(ans, str):
            ans = {"A": 0, "B": 1, "C": 2, "D": 3}.get(ans.upper(), 0)
        try:
            choice_text = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices)])
            if choices and 0 <= ans < len(choices):
                return f"Soru: {q}\nSeçenekler:\n{choice_text}\nCevap: {chr(65+ans)}. {choices[ans]}"
            return f"Soru: {q}\nSeçenekler:\n{choice_text}"
        except Exception:
            return str(row)

    # UltraChat tarzı
    if "messages" in row and isinstance(row["messages"], list) and len(row["messages"]) >= 2:
        u = row["messages"][0].get("content", "")
        a = row["messages"][1].get("content", "")
        return f"Kullanıcı: {u}\nAsistan: {a}"

    for k in ["abstract", "content", "article", "dialog", "dialogue"]:
        if k in row:
            v = row[k]
            if isinstance(v, list):
                return " ".join(map(str, v))
            return str(v)

    return str(row)


def load_dataset_with_retry(name: str, config=None, split="train"):
    """Dataset yükleme bazen patlayabiliyor; küçük retry koydum."""
    for attempt in range(MAX_RETRIES):
        try:
            return load_dataset(name, config, split=split, streaming=True, trust_remote_code=False)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = (attempt + 1) * 10
            print(f"⚠️ {name}: {str(e)[:120]} | {wait}s sonra tekrar denenecek")
            time.sleep(wait)


def count_lines(path: str) -> int:
    """Kaldığı yerden devam edebilmek için mevcut satır sayısını sayar."""
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def download_one(g: dict, seen_hashes: set):
    """Tek bir görev için: indir -> temizle -> filtrele -> yaz."""
    hedef = os.path.join(OUT_DIR, g["dosya"])
    limit = int(g.get("limit", 0))
    kategori = g.get("kategori", "Genel")
    konu = g.get("konu", "")
    split = g.get("split", "train")
    config = g.get("config", None)

    mevcut = count_lines(hedef) if os.path.exists(hedef) else 0
    if mevcut >= limit and limit > 0:
        print(f"✅ VAR: {g['dosya']} ({mevcut})")
        return hedef

    mode = "a" if mevcut > 0 else "w"
    print(f"\n⬇️ {g['dosya']} | {g['kaynak']} | {kategori} | split={split} | limit={limit} | mevcut={mevcut}")

    ds = load_dataset_with_retry(g["kaynak"], config=config, split=split)

    written = 0
    dup = 0
    skip = 0
    batch = []

    with open(hedef, mode, encoding="utf-8") as f:
        for row in ds:
            if limit and (mevcut + written) >= limit:
                break

            try:
                text = metni_temizle(parse_row_content(row))
                if not kalite_kontrolu(text, kategori):
                    skip += 1
                    continue

                h = text_hash(text)
                if h in seen_hashes:
                    dup += 1
                    continue
                seen_hashes.add(h)

                rec = {
                    "instruction": get_dynamic_instruction(kategori, text),
                    "input": f"Kaynak: {g['kaynak']}",
                    "output": text,
                    "metadata": {
                        "kategori": kategori,
                        "konu": konu,
                        "kaynak": g["kaynak"],
                        "tarih": time.strftime("%Y-%m-%d"),
                        "karakter_sayisi": len(text),
                    },
                }

                batch.append(rec)
                written += 1

                if len(batch) >= BATCH_SIZE:
                    for item in batch:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    f.flush()
                    batch = []

                if (mevcut + written) % 1000 == 0:
                    print(f"  ⏳ {mevcut+written}/{limit} (Dup:{dup} Skip:{skip})", end="\r")

                if (mevcut + written) % SLEEP_EVERY_N == 0:
                    time.sleep(SLEEP_SECS)

            except Exception:
                skip += 1
                continue

        if batch:
            for item in batch:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
            f.flush()

    print(f"\n✅ Bitti: {g['dosya']} | yazılan={written} | toplam={mevcut+written} (D:{dup} S:{skip})")
    return hedef


def main():
    ensure_dir(OUT_DIR)
    maybe_hf_login()

    # Wikipedia'yı en sona bıraktım (genelde en uzun süren/çok veri döndüren kaynak)
    wiki = [x for x in GOREVLER if "wikipedia" in x.get("kaynak", "").lower()]
    diger = [x for x in GOREVLER if "wikipedia" not in x.get("kaynak", "").lower()]

    seen_hashes = set()
    done = []

    print(f"🚀 Toplama başlıyor | out={OUT_DIR} | görev={len(GOREVLER)} | workers={WORKERS}")

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(download_one, g, seen_hashes) for g in diger]
        for fut in as_completed(futures):
            try:
                p = fut.result()
                if p:
                    done.append(p)
            except Exception as e:
                print(f"❌ Hata: {str(e)[:160]}")

    if wiki:
        print("\n🌍 Wikipedia indiriliyor...")
        try:
            p = download_one(wiki[0], seen_hashes)
            if p:
                done.append(p)
        except Exception as e:
            print(f"❌ Wikipedia hata: {str(e)[:200]}")

    print("\n" + "=" * 60)
    print(f"🎉 Tamamlandı | dosya={len(done)} | klasör={OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
