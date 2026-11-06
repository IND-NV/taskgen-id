"""Integrasi Google Gemini melalui endpoint OpenAI-compatible."""
import json
import urllib.error
import urllib.request

class GeminiError(RuntimeError):
    def __init__(self, message, status=None, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after

def _request(url, api_key, data=None, timeout=90):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        retry = exc.headers.get("Retry-After") if exc.headers else None
        try:
            retry = int(retry) if retry else None
        except ValueError:
            retry = None
        raise GeminiError(f"HTTP {exc.code}: {body[:500]}", exc.code, retry) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GeminiError(f"Koneksi Gemini gagal: {exc}") from exc

def list_models(api_base, api_key, timeout=30):
    """Ambil model dari endpoint /models; dukung bentuk OpenAI dan Gemini."""
    data = _request(api_base.rstrip("/") + "/models", api_key, timeout=timeout)
    entries = data.get("data") or data.get("models") or []
    result = []
    for item in entries:
        name = item.get("id") or item.get("name")
        if not name:
            continue
        methods = item.get("supportedGenerationMethods") or []
        if methods and not any("generateContent" in method or "chat" in method.lower() for method in methods):
            continue
        if name.startswith("models/"):
            name = name.split("/", 1)[1]
        result.append(name)
    return sorted(set(result))

def chat_completion(api_base, api_key, model, messages, temperature=0.9, timeout=90, max_tokens=4096):
    payload = json.dumps({"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}).encode("utf-8")
    data = _request(api_base.rstrip("/") + "/chat/completions", api_key, data=payload, timeout=timeout)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError(f"Format respons Gemini tidak dikenali: {str(data)[:300]}") from exc
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    usage = data.get("usage") or {}
    return str(content).strip(), int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
