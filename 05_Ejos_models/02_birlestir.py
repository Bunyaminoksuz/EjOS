# 02_birlestir.py
# Ham_Veriler altındaki tüm jsonl dosyalarını tek havuzda birleştirir.
# JSON hatalı satırları atlar, global dedupe yapar, veriyi karıştırır ve
# train/val olarak data/Egitim_Verisi altına yazar.

import os
import glob
import json
import random
import hashlib
from collections import defaultdict

DEFAULT_IN_DIR = os.path.join(os.getcwd(), "data", "Ham_Veriler")
DEFAULT_OUT_DIR = os.path.join(os.getcwd(), "data", "Egitim_Verisi")

TRAIN_RATIO = float(os.getenv("TRAIN_RATIO", "0.90"))
VAL_RATIO = float(os.getenv("VAL_RATIO", "0.10"))


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def rec_hash(rec: dict) -> str:
    """instruction+input+output üzerinden hash üretip global dedupe yapıyorum."""
    s = (
        str(rec.get("instruction", "")).strip()
        + "\n"
        + str(rec.get("input", "")).strip()
        + "\n"
        + str(rec.get("output", "")).strip()
    )
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def write_jsonl(items, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def main():
    random.seed(42)

    in_dir = os.getenv("IN_DIR", DEFAULT_IN_DIR)
    out_dir = os.getenv("OUT_DIR", DEFAULT_OUT_DIR)
    ensure_dir(out_dir)

    files = sorted(glob.glob(os.path.join(in_dir, "*.jsonl")))
    if not files:
        raise FileNotFoundError(f"❌ Ham_Veriler içinde .jsonl yok: {in_dir}")

    print(f"📂 Kaynak: {in_dir}")
    print(f"📂 Hedef : {out_dir}")
    print(f"📄 Dosya : {len(files)}")

    kategori_sayac = defaultdict(int)
    merged = []
    seen = set()
    json_err = 0

    for fp in files:
        if os.path.getsize(fp) < 100:
            continue

        added = 0
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    json_err += 1
                    continue

                h = rec_hash(rec)
                if h in seen:
                    continue
                seen.add(h)

                kat = rec.get("metadata", {}).get("kategori", "Genel")
                kategori_sayac[kat] += 1

                merged.append(rec)
                added += 1

        print(f"✅ {os.path.basename(fp)}: +{added:,}")

    print(f"\n✅ Dedupe sonrası toplam: {len(merged):,} | JSON hata: {json_err}")

    print("\n📊 Kategori dağılımı:")
    for kat, adet in sorted(kategori_sayac.items(), key=lambda x: x[1], reverse=True):
        oran = (adet / max(len(merged), 1)) * 100
        print(f"- {kat}: {adet:,} ({oran:.1f}%)")

    random.shuffle(merged)

    train_end = int(len(merged) * TRAIN_RATIO)
    val_end = train_end + int(len(merged) * VAL_RATIO)

    train = merged[:train_end]
    val = merged[train_end:val_end]

    train_path = os.path.join(out_dir, "train.jsonl")
    val_path = os.path.join(out_dir, "val.jsonl")

    write_jsonl(train, train_path)
    write_jsonl(val, val_path)

    print("\n" + "=" * 60)
    print(f"📘 train.jsonl: {len(train):,} -> {train_path}")
    print(f"📙 val.jsonl  : {len(val):,} -> {val_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
