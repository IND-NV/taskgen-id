"""Lapisan generik pembuatan batch; detail penyedia berada di folder providers."""
import json
import threading
import time
from providers.registry import get_provider

APIError = get_provider().GeminiError


class KeyRing:
    """Pemilih API key berputar; key hanya hidup di memori proses."""
    def __init__(self, keys):
        self.keys = [key.strip() for key in keys if key and key.strip()]
        if not self.keys:
            raise ValueError("Minimal satu API key Gemini diperlukan.")
        self.index = 0
        self.lock = threading.Lock()

    def next_keys(self):
        with self.lock:
            start = self.index
            self.index = (self.index + 1) % len(self.keys)
        return self.keys[start:] + self.keys[:start]


def generate_batch(api_base, keyring, model, system_prompt, specs, temperature=0.9, retries=3):
    provider = get_provider("gemini")
    labels = {
        1: "Sangat Mudah", 2: "Mudah", 3: "Dasar", 4: "Menengah", 5: "Standar",
        6: "Terampil", 7: "Mahir", 8: "Lanjut", 9: "Ahli", 10: "Sangat Ahli",
    }
    spec_lines = []
    for index, spec in enumerate(specs, 1):
        level = spec["difficulty_level"]
        spec_lines.append(
            f"{index}. Kategori: {spec['main_category']}\n"
            f"   Bidang: {spec['domain']}\n"
            f"   Subbidang: {spec['subdomain']}\n"
            f"   Kesulitan: {level}/10 ({labels[level]})"
        )

    user_prompt = (
        f"Buat tepat {len(specs)} pesan pengguna yang berbeda berdasarkan spesifikasi berikut:\n"
        + "\n".join(spec_lines)
        + "\nWAJIB: seluruh pesan harus sepenuhnya menggunakan bahasa Indonesia, bukan campuran "
          "Indonesia-Inggris. Jangan menyalin label kategori atau bidang yang berbahasa Inggris "
          "ke dalam pesan; pahami maknanya dan tulis secara alami dalam bahasa Indonesia. "
          "Keluarkan HANYA larik JSON valid berisi tepat jumlah pesan tersebut, tanpa teks tambahan."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None
    for attempt in range(retries + 1):
        round_errors = []
        retry_round = False
        for api_key in keyring.next_keys():
            try:
                content, input_tokens, output_tokens = provider.chat_completion(
                    api_base, api_key, model, messages, temperature
                )
                clean = content.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                try:
                    prompts = json.loads(clean)
                except json.JSONDecodeError as exc:
                    raise APIError(f"Gemini mengembalikan JSON tidak valid: {exc}") from exc

                if (
                    not isinstance(prompts, list)
                    or len(prompts) != len(specs)
                    or any(not isinstance(prompt, str) or not prompt.strip() for prompt in prompts)
                ):
                    raise APIError(
                        f"Respons harus berupa array berisi {len(specs)} teks tidak kosong."
                    )
                return prompts, input_tokens, output_tokens

            except APIError as exc:
                last_error = exc
                round_errors.append(exc)
                if exc.status in (401, 403, 429):
                    continue
                if exc.status is None or exc.status in (408, 425) or exc.status >= 500:
                    retry_round = True
                    break
                raise

        if round_errors and all(error.status in (401, 403) for error in round_errors):
            raise last_error
        if not retry_round and round_errors and all(
            error.status in (401, 403, 429) for error in round_errors
        ):
            retry_round = any(error.status == 429 for error in round_errors)
        if not retry_round or attempt == retries:
            raise last_error or APIError("Permintaan Gemini gagal.")

        wait = last_error.retry_after if last_error and last_error.retry_after else min(2 ** (attempt + 1), 20)
        time.sleep(wait)

    raise last_error or APIError("Batas percobaan terlampaui.")
