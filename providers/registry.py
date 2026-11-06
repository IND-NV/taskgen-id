"""Daftar penyedia API. Tambahkan modul baru dan daftarkan di sini."""
from . import gemini

PROVIDERS = {"gemini": gemini}
DEFAULT_PROVIDER = "gemini"

def get_provider(name=DEFAULT_PROVIDER):
    try:
        return PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"Penyedia API tidak dikenal: {name}") from exc
