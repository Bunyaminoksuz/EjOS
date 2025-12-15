# 03_cevir_tr.py
# Eğitim setindeki instruction/input/output alanlarını Argos Translate ile EN->TR çevirir.
# RAM şişmemesi için dosyayı satır satır işler (stream).

import os
import json
import argparse

import argostranslate.package
import argostranslate.translate


def install_argos_en_tr():
    """İlk seferde Argos en->tr paketini kurar."""
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next(p for p in available if p.from_code == "en" and p.to_code == "tr")
    argostranslate.package.install_from_path(pkg.download())


def tr(text: str) -> str:
    """Boş değilse çevir; hata olursa metni olduğu gibi bırak."""
    if not text or not str(text).strip():
        return ""
    try:
        return argostranslate.translate.translate(str(text), "en", "tr")
    except Exception:
        return str(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Örn: data/Egitim_Verisi/train.jsonl")
    ap.add_argument("--output", required=True, help="Örn: data/Egitim_Verisi/train_tr.jsonl")
    ap.add_argument("--no_install", action="store_true", help="Kurulumu atla (paket zaten kuruluysa)")
    ap.add_argument("--fields", default="instruction,input,output", help="Çevrilecek alanlar (csv)")
    args = ap.parse_args()

    if not args.no_install:
        print("📥 Argos en->tr paketi kuruluyor...")
        install_argos_en_tr()
        print("✅ Argos hazır")

    fields = [x.strip() for x in args.fields.split(",") if x.strip()]
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    n_ok = 0
    n_bad = 0

    with open(args.input, "r", encoding="utf-8") as fin, open(args.output, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                n_bad += 1
                continue

            for f in fields:
                rec[f] = tr(rec.get(f, ""))

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_ok += 1

            if n_ok % 500 == 0:
                print(f"⏳ {n_ok} satır", end="\r")

    print(f"\n🎉 Çeviri bitti: {n_ok:,} satır | hatalı: {n_bad:,}")
    print(f"📄 Output: {args.output}")


if __name__ == "__main__":
    main()
