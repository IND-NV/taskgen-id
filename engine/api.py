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
    labels = {1:"Very Easy",2:"Easy",3:"Basic",4:"Intermediate",5:"Standard",6:"Skilled",7:"Proficient",8:"Advanced",9:"Expert",10:"Polymath"}
    for i, spec in enumerate(specs, 1):
        level = spec["difficulty_level"]
        spec_lines.append(f"{i}. Main category: {spec['main_category']}\n   Domain: {spec['domain']}\n   Subdomain: {spec['subdomain']}\n   Difficulty: {level}/10 ({labels[level]})")
    user_prompt = (f"Generate exactly {len(specs)} distinct task prompts for these specifications:\n" + "\n".join(spec_lines) + "\nAll prompts must be in Indonesian. Each must focus on its own subdomain and difficulty. Return ONLY a valid JSON array containing exactly that many strings.")
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
