"""Pemilihan kategori, domain, subdomain, dan level."""
import random
from categories.registry import DEFAULT_DISTRIBUTION, get_domains
from .config import DEFAULT_DIFFICULTY


def _weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


def build_domain_pool(distribution=None):
    distribution = distribution or DEFAULT_DISTRIBUTION
    domains = get_domains(distribution.keys())
    pool = []
    for category, category_weight in distribution.items():
        cat_domains = [d for d in domains if d["category"] == category]
        if not cat_domains:
            raise ValueError(f"Kategori tidak dikenal atau tidak punya domain: {category}")
        for domain in cat_domains:
            subdomains = domain["subdomains"]
            weight = category_weight / len(cat_domains) / len(subdomains)
            for subdomain in subdomains:
                pool.append((domain["category_name"], domain["name"], subdomain, weight))
    return pool


def sample_spec(pool):
    difficulty = DEFAULT_DIFFICULTY
    category, domain, subdomain, _ = _weighted_choice(
        pool, [item[3] for item in pool]
    )
    level = _weighted_choice(list(difficulty), list(difficulty.values()))
    return {
        "main_category": category,
        "domain": domain,
        "subdomain": subdomain,
        "difficulty_level": level,
    }
