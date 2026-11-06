"""Registry kategori bawaan TaskGen-ID."""

from .coding import CATEGORY as CODING
from .conversation import CATEGORY as CONVERSATION
from .creative import CATEGORY as CREATIVE
from .cs import CATEGORY as CS
from .math import CATEGORY as MATH
from .science import CATEGORY as SCIENCE

BUILTIN_CATEGORIES = (
    MATH,
    CODING,
    SCIENCE,
    CS,
    CREATIVE,
    CONVERSATION,
)

# ID internal tetap stabil untuk konfigurasi, distribusi, dan CLI.
DEFAULT_DISTRIBUTION = {
    "math": 0.25,
    "coding": 0.25,
    "science": 0.15,
    "cs": 0.15,
    "creative": 0.10,
    "conversation": 0.10,
}


def get_categories():
    """Kembalikan kategori bawaan berdasarkan ID internal."""
    return {category["id"]: category for category in BUILTIN_CATEGORIES}


def get_domains(category_ids=None):
    """Kembalikan domain dan label kategori dalam bahasa Indonesia."""
    selected = set(category_ids) if category_ids is not None else None
    result = []
    for category in BUILTIN_CATEGORIES:
        if selected is not None and category["id"] not in selected:
            continue
        for domain in category["domains"]:
            result.append({
                "category": category["id"],
                "category_name": category["name"],
                "name": domain["name"],
                "subdomains": list(domain["subdomains"]),
            })
    return result
