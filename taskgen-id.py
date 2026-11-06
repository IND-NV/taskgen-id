#!/usr/bin/env python3
"""TaskGen-ID — CLI Python, tanpa dependensi pihak ketiga."""
import argparse
import getpass
import os
import sys
from categories.registry import get_categories
from engine.config import DEFAULT_API_BASE, DEFAULT_MODEL, DEFAULT_WORKERS
from engine.generator import run_generation, parse_weights


def build_parser():
    parser = argparse.ArgumentParser(description="Generator dataset pertanyaan sintetis Indonesia (Python).")
    parser.add_argument("-c", "--count", type=int, default=250, help="Jumlah pertanyaan yang dibuat")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help="Worker paralel (Termux: 1-2)")
    parser.add_argument("-b", "--batch-size", type=int, default=2, help="Jumlah pertanyaan per request API")
    parser.add_argument("-o", "--output", default="output.json", help="Lokasi file JSON")
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY"), help="API key (atau env GEMINI_API_KEY)")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("-t", "--temperature", type=float, default=.9)
    parser.add_argument("--categories", help="Kategori dipisah koma, misalnya math,coding")
    parser.add_argument("--distribution", help="Bobot kategori: math=0.5,coding=0.5")
    parser.add_argument("--difficulty", help="Bobot level: 1=0.1,2=0.2,...")
    parser.add_argument("--system-prompt", help="File prompt khusus")
    parser.add_argument("--delay", type=float, default=3, help="Jeda per worker setelah batch")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        print("\n=== TaskGen-ID | Python ===")
        print("Mode interaktif (aman untuk Termux / RAM kecil)")
        try:
            raw = input("Jumlah pertanyaan [10]: ").strip()
            args.count = int(raw) if raw else 10
            raw = input("Worker [1]: ").strip()
            args.workers = int(raw) if raw else 1
            raw = input("Batch per request [2]: ").strip()
            args.batch_size = int(raw) if raw else 2
            raw = input("Kategori (kosong = semua) [math,coding,science,cs,creative,conversation]: ").strip()
            args.categories = raw or None
            raw = input("Nama file output [output.json]: ").strip()
            args.output = raw or "output.json"
        except (ValueError, EOFError):
            print("Input tidak valid."); return 2
    if not args.api_key:
        args.api_key = getpass.getpass("Gemini API key: ").strip()
    distribution = parse_weights(args.distribution) if args.distribution else None
    difficulty = parse_weights(args.difficulty, int) if args.difficulty else None
    prompt = None
    if args.system_prompt:
        with open(args.system_prompt, encoding="utf-8") as handle: prompt = handle.read()
    categories = [x.strip() for x in args.categories.split(",")] if args.categories else None
    print("TaskGen-ID Python | standard library only")
    print(f"Kategori tersedia: {', '.join(get_categories())}")
    print(f"Target: {args.count} | workers: {args.workers} | batch: {args.batch_size}")
    try:
        stats = run_generation(count=args.count, api_key=args.api_key, api_base=args.api_base, model=args.model, output=args.output, workers=args.workers, batch_size=args.batch_size, temperature=args.temperature, categories=categories, distribution=distribution, difficulty=difficulty, system_prompt=prompt, delay=args.delay)
    except KeyboardInterrupt:
        print("\nDihentikan pengguna."); return 130
    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr); return 1
    print(f"Selesai: {stats['done']} pertanyaan | error: {stats['errors']} | token masuk/keluar: {stats['input_tokens']}/{stats['output_tokens']}")
    print(f"Output: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
