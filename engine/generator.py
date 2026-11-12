"""Orkestrasi generator dengan antrean terbatas dan penyimpanan per batch."""
import concurrent.futures
import time
from .api import generate_batch, KeyRing
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


def run_generation(count=250, api_key=None, api_keys=None, api_base=None, model=None, output="output.json", workers=1, batch_size=2, temperature=.9, categories=None, distribution=None, system_prompt=None, delay=3, progress=print):
    from .config import DEFAULT_API_BASE, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT
    keys = api_keys or ([api_key] if api_key else [])
    keyring = KeyRing(keys)
    if count < 1 or batch_size < 1 or workers < 1:
        raise ValueError("Jumlah data, batch, dan worker harus lebih besar dari nol.")

    dist = distribution or dict(DEFAULT_DISTRIBUTION)
    if categories:
        dist = {key: value for key, value in dist.items() if key in categories}
        if not dist:
            raise ValueError("Tidak ada kategori valid yang dipilih.")
        total = sum(dist.values())
        dist = {key: value / total for key, value in dist.items()}

    pool = build_domain_pool(dist)
    records = load_records(output)
    next_id = max(
        (int(record.get("id", "0")) for record in records
         if str(record.get("id", "0")).isdigit()),
        default=0,
    ) + 1

    api_base = api_base or DEFAULT_API_BASE
    model = model or DEFAULT_MODEL
    if not model:
        raise ValueError("Nama model Gemini wajib diisi.")
    system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    stats = {"done": 0, "input_tokens": 0, "output_tokens": 0, "errors": 0}
    total_batches = (count + batch_size - 1) // batch_size

    def batches():
        remaining = count
        while remaining:
            size = min(batch_size, remaining)
            yield [sample_spec(pool) for _ in range(size)]
            remaining -= size

    batch_iterator = iter(batches())
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {}

        def submit_one():
            try:
                specs = next(batch_iterator)
            except StopIteration:
                return False
            future = executor.submit(
                generate_batch, api_base, keyring, model, system_prompt, specs, temperature
            )
            pending[future] = specs
            return True

        for _ in range(workers):
            if not submit_one():
                break

        finished_batches = 0
        stop_submitting = False
        while pending:
            completed, _ = concurrent.futures.wait(
                pending, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in completed:
                specs = pending.pop(future)
                if future.cancelled():
                    continue
                finished_batches += 1
                try:
                    prompts, input_tokens, output_tokens = future.result()
                except Exception as exc:
                    stats["errors"] += 1
                    progress(f"[GALAT] {exc}")
                    stop_submitting = True
                    for queued in pending:
                        queued.cancel()
                else:
                    for prompt, spec in zip(prompts, specs):
                        records.append(make_record(prompt, spec, next_id))
                        next_id += 1
                    save_records(output, records)
                    stats["done"] += len(prompts)
                    stats["input_tokens"] += input_tokens
                    stats["output_tokens"] += output_tokens
                    progress(f"Progres: {stats['done']}/{count}")

                if not stop_submitting and finished_batches < total_batches and delay:
                    time.sleep(delay)
                if not stop_submitting:
                    submit_one()

    return stats
