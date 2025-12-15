# 04_train.py
# Unsloth + TRL ile LoRA fine-tune yapar ve sadece adapter ağırlıklarını kaydeder.
# GGUF üretmez; GGUF için 05_export_gguf.py kullanılır.

import os
import argparse
import random
import gc

import numpy as np
import torch

from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from huggingface_hub import login

from unsloth import FastLanguageModel, is_bfloat16_supported


def maybe_hf_login():
    """HF_TOKEN varsa login olur (opsiyonel)."""
    token = os.getenv("HF_TOKEN", "").strip()
    if token:
        try:
            login(token=token)
        except Exception as e:
            print(f"⚠️ HF login başarısız: {str(e)[:160]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_path", required=True, help="Örn: data/Egitim_Verisi/train_tr.jsonl")
    ap.add_argument("--run_name", default="EJOS_v1")
    ap.add_argument("--base_model", default="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit")
    ap.add_argument("--max_seq_length", type=int, default=2048)
    ap.add_argument("--max_steps", type=int, default=4000)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=3407)
    ap.add_argument("--bs", type=int, default=2)
    ap.add_argument("--grad_acc", type=int, default=4)
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--save_total_limit", type=int, default=2)
    ap.add_argument("--out_dir", default="", help="Boşsa: ./runs/{run_name}")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    os.environ["WANDB_DISABLED"] = "true"
    os.environ["WANDB_MODE"] = "disabled"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    else:
        raise RuntimeError("❌ GPU bulunamadı")

    maybe_hf_login()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
        use_rslora=False,
        loftq_config=None,
    )

    alpaca_prompt = """Sen uzman bir Elektrik-Elektronik Mühendisi ve Fizikçisin.
Bilgi dağarcığın İngilizce teknik kaynaklara dayanır ancak kullanıcıyla DAİMA TÜRKÇE konuşursun.
Teknik terimleri (Op-Amp, MOSFET, Quantum vb.) orijinal haliyle kullanıp açıklamalarını Türkçe yaparsın.
Asla İngilizce cevap verme.
### Instruction:
{}
### Input:
{}
### Response:
{}"""
    EOS_TOKEN = tokenizer.eos_token

    def formatting_prompts_func(examples):
        inst = examples.get("instruction", [])
        inp = examples.get("input", [])
        out = examples.get("output", [])
        texts = []
        for a, b, c in zip(inst, inp, out):
            b = b if b and str(b).strip() else "YOK"
            texts.append(alpaca_prompt.format(a, b, c) + EOS_TOKEN)
        return {"text": texts}

    ds = load_dataset("json", data_files=args.dataset_path, split="train")
    ds = ds.map(formatting_prompts_func, batched=True, remove_columns=ds.column_names)
    print(f"✅ Dataset: {len(ds):,} satır")

    max_steps = min(args.max_steps, len(ds) * 2)

    out_dir = args.out_dir.strip() or os.path.join(os.getcwd(), "runs", args.run_name)
    os.makedirs(out_dir, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=1,
        packing=True,
        args=TrainingArguments(
            output_dir=out_dir,
            per_device_train_batch_size=args.bs,
            gradient_accumulation_steps=args.grad_acc,
            warmup_steps=100,
            learning_rate=args.lr,
            max_steps=max_steps,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=10,
            save_steps=args.save_steps,
            save_total_limit=args.save_total_limit,
            eval_strategy="no",
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=args.seed,
            report_to="none",
        ),
    )

    print(f"▶ Eğitim başlıyor: max_steps={max_steps}")
    trainer.train()

    final_dir = os.path.join(out_dir, "final_adapter")
    os.makedirs(final_dir, exist_ok=True)
    model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"✅ Eğitim bitti. Adapter çıktı: {final_dir}")


if __name__ == "__main__":
    main()
