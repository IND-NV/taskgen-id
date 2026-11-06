#!/usr/bin/env python3
"""TaskGen-ID — CLI interaktif, tanpa dependensi pihak ketiga."""
import argparse
import getpass
import os
import sys
from categories.registry import get_categories
from engine.config import DEFAULT_API_BASE, DEFAULT_MODEL, DEFAULT_WORKERS
from engine.generator import run_generation, parse_weights
from providers.registry import get_provider


def build_parser():
    parser = argparse.ArgumentParser(description="Generator dataset pertanyaan sintetis Indonesia.")
    parser.add_argument("-c", "--count", type=int, default=250, help="Jumlah pertanyaan")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Worker paralel (Termux: 1-2)")
    parser.add_argument("-b", "--batch-size", type=int, default=2, help="Jumlah pertanyaan per permintaan")
    parser.add_argument("-o", "--output", default="output.json", help="Berkas keluaran")
    parser.add_argument("--api-key", action="append", help="API key Gemini; dapat diulang")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("-m", "--model", default=None)
    parser.add_argument("-t", "--temperature", type=float, default=.9)
    parser.add_argument("--categories", help="ID kategori dipisahkan koma, misalnya math,coding")
    parser.add_argument("--distribution", help="Bobot kategori: math=0.5,coding=0.5")
    parser.add_argument("--difficulty", help="Bobot tingkat: 1=0.1,2=0.2,...")
    parser.add_argument("--system-prompt", help="Berkas instruksi khusus")
    parser.add_argument("--delay", type=float, default=3, help="Jeda antarbatch")
    return parser


def ask_api_keys():
    keys = []
    print("\nMasukkan API key Gemini. Kosongkan untuk selesai.")
    while True:
        key = getpass.getpass(f"API key {len(keys) + 1}: ").strip()
        if not key:
            if keys: break
            print("Masukkan minimal satu API key.")
            continue
        if key not in keys:
            keys.append(key)
        else:
            print("Key ini sudah dimasukkan.")
    return keys


def choose_model(api_base, api_key, supplied=None):
    if supplied:
        return supplied
    provider = get_provider("gemini")
    try:
        models = provider.list_models(api_base, api_key)
    except Exception as exc:
        print(f"Tidak bisa mengambil daftar model: {exc}")
        models = []
    if models:
        print("\nModel Gemini yang tersedia:")
        for index, model in enumerate(models, 1):
            print(f"{index}. {model}")
        print("M. Masukkan nama model secara manual")
        while True:
            choice = input("Pilih model [1]: ").strip() or "1"
            if choice.lower() == "m":
                manual = input("Nama model: ").strip()
                if manual: return manual
            elif choice.isdigit() and 1 <= int(choice) <= len(models):
                return models[int(choice) - 1]
            print("Pilihan tidak valid.")
    return input(f"Nama model Gemini [{DEFAULT_MODEL}]: ").strip() or DEFAULT_MODEL


def main():
    parser = build_parser()
    args = parser.parse_args()
    interactive = len(sys.argv) == 1
    keys = args.api_key or []
    if interactive:
        print("\n=== TASKGEN-ID | PYTHON ===")
        print("Penyedia aktif: Google Gemini")
        keys = ask_api_keys()
        args.model = choose_model(args.api_base, keys[0], args.model)
        try:
            raw = input("Jumlah pertanyaan [10]: ").strip(); args.count = int(raw) if raw else 10
            raw = input("Worker [1]: ").strip(); args.workers = int(raw) if raw else 1
            raw = input("Batch per permintaan [2]: ").strip(); args.batch_size = int(raw) if raw else 2
            labels = get_categories()
            print("\nKategori:")
            for index, (key, value) in enumerate(labels.items(), 1): print(f"{index}. {value['name']}")
            print("0. Semua kategori")
            raw = input("Pilih nomor kategori dipisahkan koma [0]: ").strip()
            if raw and raw != "0":
                ordered = list(labels)
                args.categories = ",".join(ordered[int(x.strip()) - 1] for x in raw.split(",") if x.strip().isdigit() and 1 <= int(x.strip()) <= len(ordered))
            raw = input("Nama berkas keluaran [output.json]: ").strip(); args.output = raw or "output.json"
        except (ValueError, EOFError, IndexError):
            print("Masukan tidak valid."); return 2
    if not keys:
        keys = ask_api_keys()
    model = args.model or choose_model(args.api_base, keys[0])
    distribution = parse_weights(args.distribution) if args.distribution else None
    difficulty = parse_weights(args.difficulty, int) if args.difficulty else None
    prompt = None
    if args.system_prompt:
        with open(args.system_prompt, encoding="utf-8") as handle: prompt = handle.read()
    categories = [x.strip() for x in args.categories.split(",")] if args.categories else None
    print(f"Model: {model} | jumlah key aktif: {len(keys)}")
    try:
        stats = run_generation(count=args.count, api_keys=keys, api_base=args.api_base, model=model, output=args.output, workers=args.workers, batch_size=args.batch_size, temperature=args.temperature, categories=categories, distribution=distribution, difficulty=difficulty, system_prompt=prompt, delay=args.delay)
    except KeyboardInterrupt:
        print("\nDihentikan pengguna."); return 130
    except Exception as exc:
        print(f"[GAGAL] {exc}", file=sys.stderr); return 1
    print(f"Selesai: {stats['done']} pertanyaan | galat: {stats['errors']} | token masuk/keluar: {stats['input_tokens']}/{stats['output_tokens']}")
    print(f"Hasil: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
