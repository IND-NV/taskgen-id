"""Kategori sains TaskGen-ID."""

CATEGORY = {
    "id": "science",
    "name": "Sains",
    "domains": [
        {"name": "Fisika", "subdomains": ["mekanika", "termodinamika", "elektromagnetisme", "kuantum", "relativitas", "optika", "dinamika_fluida"]},
        {"name": "Kimia", "subdomains": ["organik", "anorganik", "fisik", "analitik", "biokimia", "elektrokimia"]},
        {"name": "Biologi", "subdomains": ["genetika", "ekologi", "biologi_sel", "evolusi", "mikrobiologi", "neurosains", "imunologi"]},
        {"name": "Ilmu Kebumian", "subdomains": ["geologi", "meteorologi", "oseanografi", "iklim", "mineralogi", "vulkanologi"]},
        {"name": "Astronomi", "subdomains": ["bintang", "keplanetan", "kosmologi", "astrofisika", "pengamatan", "astrobiologi"]},
    ],
}
