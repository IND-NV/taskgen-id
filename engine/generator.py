"""Orkestrasi generator; hasil ditulis setiap batch selesai."""
import concurrent.futures
import threading
from .api import generate_batch
from .sampler import build_domain_pool, sample_spec
from .storage import load_records, save_records, make_record
from categories.registry import DEFAULT_DISTRIBUTION
from .config import DEFAULT_DIFFICULTY


def parse_weights(value, cast_key=str):
    result = {}
    for part in value.split(","):
        key, weight = part.split("=", 1)
        result[cast_key(key.strip().lstrip("dD"))] = float(weight)
    total = sum(result.values())
    if total <= 0 or any(v < 0 for v in result.values()) or abs(total - 1.0) > .05:
        raise ValueError("Bobot harus non-negatif dan totalnya mendekati 1.0.")
    return {k: v / total for k, v in result.items()}


def run_generation(count=250, api_key=None, api_base=None, model=None, output="output.json", workers=1, batch_size=2, temperature=.9, categories=None, distribution=None, difficulty=None, system_prompt=None, delay=3, progress=print):
    from .config import DEFAULT_API_BASE, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT
    if not api_key:
        raise ValueError("API key belum diatur. Isi GEMINI_API_KEY atau gunakan --api-key.")
    if count < 1 or batch_size < 1 or workers < 1:
        raise ValueError("count, batch-size, dan workers harus lebih besar dari nol.")
    dist = distribution or dict(DEFAULT_DISTRIBUTION)
    if categories:
        dist = {k: v for k, v in dist.items() if k in categories}
        if not dist: raise ValueError("Tidak ada kategori valid yang dipilih.")
        total = sum(dist.values()); dist = {k:v/total for k,v in dist.items()}
    diff = difficulty or DEFAULT_DIFFICULTY
    pool = build_domain_pool(dist)
    records = load_records(output)
    next_id = max((int(r.get("id", "0")) for r in records if str(r.get("id", "0")).isdigit()), default=0) + 1
    lock = threading.Lock()
    stop = threading.Event()
    stats = {"done":0,"input_tokens":0,"output_tokens":0,"errors":0}
    batches = []
    remaining = count
    while remaining:
        size = min(batch_size, remaining)
        batches.append([sample_spec(pool, diff) for _ in range(size)])
        remaining -= size
    def task(specs):
        if stop.is_set(): return None
        try:
            result = generate_batch(api_base or DEFAULT_API_BASE, api_key, model or DEFAULT_MODEL, system_prompt or DEFAULT_SYSTEM_PROMPT, specs, temperature)
            prompts, in_tokens, out_tokens = result
            with lock:
                nonlocal next_id
                for prompt, spec in zip(prompts, specs):
                    records.append(make_record(prompt, spec, next_id)); next_id += 1
                    stats["done"] += 1
                    save_records(output, records)
                stats["input_tokens"] += in_tokens; stats["output_tokens"] += out_tokens
                progress(f"Progress: {stats['done']}/{count}")
            if delay: import time; time.sleep(delay)
            return True
        except Exception as exc:
            with lock:
                stats["errors"] += 1
                progress(f"[ERROR] {exc}")
            if getattr(exc, "status", None) in (401,402,403): stop.set()
            return False
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(task, specs) for specs in batches]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return stats
