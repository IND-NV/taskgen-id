"""Klien chat-completions menggunakan urllib (tanpa dependensi eksternal)."""
import json
import time
import urllib.error
import urllib.request


class APIError(RuntimeError):
    def __init__(self, message, status=None, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


def chat_completion(api_base, api_key, model, messages, temperature=0.9, timeout=90, max_tokens=4096):
    url = api_base.rstrip("/") + "/chat/completions"
    payload = json.dumps({"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}).encode()
    request = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        retry = exc.headers.get("Retry-After") if exc.headers else None
        try: retry = int(retry) if retry else None
        except ValueError: retry = None
        raise APIError(f"HTTP {exc.code}: {body[:600]}", exc.code, retry) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise APIError(f"Koneksi API gagal: {exc}") from exc
    try:
        choice = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise APIError(f"Format respons API tidak dikenali: {str(data)[:400]}") from exc
    usage = data.get("usage") or {}
    return choice.strip(), int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))


def generate_batch(api_base, api_key, model, system_prompt, specs, temperature=0.9, retries=4, delay=3):
    spec_lines = []
    labels = {1:"Sangat Mudah",2:"Mudah",3:"Dasar",4:"Menengah",5:"Standar",6:"Terampil",7:"Mahir",8:"Lanjut",9:"Ahli",10:"Sangat Ahli"}
    for i, spec in enumerate(specs, 1):
        level = spec["difficulty_level"]
        spec_lines.append(f"{i}. Kategori utama: {spec['main_category']}\n   Bidang: {spec['domain']}\n   Subbidang: {spec['subdomain']}\n   Tingkat kesulitan: {level}/10 ({labels[level]})")
    user_prompt = (f"Buat tepat {len(specs)} pesan pengguna yang berbeda berdasarkan spesifikasi berikut:\n" + "\n".join(spec_lines) + "\nWAJIB: seluruh pesan harus sepenuhnya menggunakan bahasa Indonesia, bukan campuran Indonesia-Inggris. Jangan menyalin label kategori atau bidang yang berbahasa Inggris ke dalam pesan; pahami maknanya dan tulis secara alami dalam bahasa Indonesia. Setiap pesan harus sesuai dengan subbidang dan tingkat kesulitannya sendiri. Keluarkan HANYA larik JSON valid yang berisi tepat sejumlah string tersebut, tanpa teks tambahan.")
    messages = [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]
    for attempt in range(retries + 1):
        try:
            content, input_tokens, output_tokens = chat_completion(api_base, api_key, model, messages, temperature)
            clean = content.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            prompts = json.loads(clean)
            if not isinstance(prompts, list) or len(prompts) != len(specs) or any(not isinstance(p, str) or not p.strip() for p in prompts):
                raise APIError(f"Respons harus berupa array berisi {len(specs)} string tidak kosong.")
            return prompts, input_tokens, output_tokens
        except APIError as exc:
            if exc.status == 429 and attempt < retries:
                wait = exc.retry_after or delay
            elif (exc.status is None or exc.status >= 500) and attempt < retries:
                wait = min(2 ** (attempt + 1), 30)
            else:
                raise
            time.sleep(wait)
    raise APIError("Batas retry terlampaui.")
