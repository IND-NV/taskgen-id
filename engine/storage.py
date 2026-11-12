"""Penyimpanan dataset JSON dengan penyimpanan atomik."""
import json
import os
import tempfile

FIELDS = ("question", "language", "main_category", "domain", "subdomain", "id")


def load_records(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("File output harus berupa JSON array.")
    # Hilangkan kolom lama agar dataset lama ikut mengikuti skema terbaru.
    return [
        {field: record[field] for field in FIELDS if field in record}
        for record in data
    ]


def save_records(path, records):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".taskgen-", suffix=".tmp", dir=folder, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def make_record(question, spec, record_id):
    record = {
        "question": question.strip(),
        "language": "Indonesia",
        **spec,
        "id": f"{record_id:06d}",
    }
    return {field: record[field] for field in FIELDS}
