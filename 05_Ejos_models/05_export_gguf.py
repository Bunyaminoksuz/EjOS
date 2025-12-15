# 05_export_gguf.py
# 04_train.py çıktısı olan LoRA adapter'ı base modele PEFT ile bağlar ve GGUF export yapar.
# Çıktı exports/<out_name>.gguf olur.

import os
import glob
import argparse
import gc
import torch

from huggingface_hub import login
from unsloth import FastLanguageModel


def maybe_hf_login():
    token = os.getenv("HF_TOKEN", "").strip()
    if token:
        try:
            login(token=token)
        except Exception as e:
            print(f"⚠️ HF login başarısız: {str(e)[:160]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", default="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit")
    ap.add_argument("--adapter_dir", required=True, help="Örn: runs/EJOS_v1/final_adapter")
    ap.add_argument("--out_name", default="EJOS_v1")
    ap.add_argument("--quant", default="q4_k_m")
    ap.add_argument("--max_seq_length", type=int, default=2048)
    ap.add_argument("--out_dir", default="", help="Boşsa: ./exports")
    args = ap.parse_args()

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    else:
        raise RuntimeError("❌ GPU bulunamadı")

    maybe_hf_login()

    base_model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    # LoRA adapter'ı base modele bağla
    from peft import PeftModel
    model = PeftModel.from_pretrained(base_model, args.adapter_dir)

    export_dir = args.out_dir.strip() or os.path.join(os.getcwd(), "exports")
    os.makedirs(export_dir, exist_ok=True)

    tmp_dir = os.path.join(export_dir, f"{args.out_name}_gguf_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"💾 GGUF export: quant={args.quant}")
    model.save_pretrained_gguf(tmp_dir, tokenizer, quantization_method=args.quant)

    ggufs = glob.glob(os.path.join(tmp_dir, "*.gguf"))
    if not ggufs:
        raise RuntimeError("❌ GGUF üretilmedi")

    final = os.path.join(export_dir, f"{args.out_name}.gguf")
    os.replace(ggufs[0], final)
    print(f"✅ GGUF hazır: {final}")


if __name__ == "__main__":
    main()
