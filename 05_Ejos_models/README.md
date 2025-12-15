# EJOS Dataset Pipeline (Topla → Birleştir → Çevir → Eğit → GGUF)

Bu repo 5 adet Python scriptiyle uçtan uca veri hazırlama ve LoRA fine-tune pipeline’ı kurar. Scriptler içinde hardcode token yoktur; gerekiyorsa yalnızca `HF_TOKEN` ortam değişkeni üzerinden Hugging Face login yapılır.

## Dosyalar
- `01_dataset_topla.py`: Dataset indirir, temizler, kalite filtresi uygular, dedupe yapar ve `data/Ham_Veriler/*.jsonl` üretir.
- `02_birlestir.py`: `data/Ham_Veriler/*.jsonl` dosyalarını birleştirir, global dedupe + shuffle yapar, `data/Egitim_Verisi/train.jsonl` ve `val.jsonl` yazar.
- `03_en_tr_ceviri.py`: JSONL’i satır satır çevirir (EN→TR). RAM şişirmemek için stream eder.
- `04_egitim.py`: Unsloth + TRL ile LoRA SFT eğitimi yapar; `runs/<run_name>/final_adapter` çıktısını üretir.
- `05_export_gguf.py`: Adapter’ı base modele bağlar ve GGUF export alır; `exports/<out_name>.gguf` üretir.

## Klasör yapısı (çıktılar)
- `data/Ham_Veriler/`: Toplanan ham jsonl dosyaları.
- `data/Egitim_Verisi/`: Birleştirilmiş train/val jsonl dosyaları.
- `runs/`: Eğitim çıktıları + `final_adapter`.
- `exports/`: GGUF çıktısı.

## Kurulum
Python 3.10+ önerilir.

Gerekli paketler (özet):
- `datasets`, `huggingface_hub`
- `argostranslate`
- `torch` (CUDA’lı)
- `transformers`, `trl`, `peft`, `unsloth`

> HF gated model/dataset kullanacaksan:
- Linux/macOS: `export HF_TOKEN="..."`
- Windows (PowerShell): `$env:HF_TOKEN="..."`

## Uçtan uca kullanım

### 1) Dataset topla

```bash
python 01_dataset_topla.py
```

Çıktı: `data/Ham_Veriler/*.jsonl`

### 2) Birleştir ve train/val ayır
```bash
python 02_birlestir.py
```

Çıktı: `data/Egitim_Verisi/train.jsonl` ve `data/Egitim_Verisi/val.jsonl`

İsteğe bağlı environment ayarları (örnek):
```bash
export TRAIN_RATIO=0.90
export VAL_RATIO=0.10
```


### 3) EN→TR çeviri (opsiyonel ama önerilir)
```bash
python 03_en_tr_ceviri.py --input data/Egitim_Verisi/train.jsonl --output data/Egitim_Verisi/train_tr.jsonl
```

```bash
python 03_en_tr_ceviri.py --input data/Egitim_Verisi/val.jsonl --output data/Egitim_Verisi/val_tr.jsonl
```

Paket zaten kuruluysa:
```bash
python 03_en_tr_ceviri.py --no_install --input data/Egitim_Verisi/train.jsonl --output data/Egitim_Verisi/train_tr.jsonl
```


### 4) LoRA fine-tune
```bash
python 04_egitim.py --datasetpath data/Egitim_Verisi/train_tr.jsonl --runname EJOS_v1
```

Çıktı: `runs/EJOS_v1/final_adapter`

> Not: CUDA’lı GPU yoksa script hata verir.

### 5) GGUF export
```bash
python 05_export_gguf.py --adapterdir runs/EJOS_v1/final_adapter --outname EJOS_v1

```

Çıktı: `exports/EJOS_v1.gguf`

Quant değiştirme örneği:
```bash
python 05_export_gguf.py --adapterdir runs/EJOS_v1/final_adapter --outname EJOS_v1 --quant q4_k_m
```


## Güvenlik notu (GitHub için)
Bu 5 script içinde hardcode token yoktur; `HF_TOKEN` sadece environment variable’dan okunur.

## .gitignore önerisi
data/
runs/
exports/
*.jsonl
*.gguf
__pycache__/
.venv/
.DS_Store

