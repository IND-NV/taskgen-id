"""Kategori percakapan dan bantuan interpersonal TaskGen-ID."""

CATEGORY = {
    "id": "conversation",
    "name": "Percakapan",
    "domains": [
        {"name": "Debat", "subdomains": ["formal", "santai", "filosofis", "ilmiah", "politik", "etika"]},
        {"name": "Saran", "subdomains": ["karier", "hubungan", "akademik", "keuangan", "kesehatan", "teknis"]},
        {"name": "Wawancara", "subdomains": ["pekerjaan", "podcast", "jurnalistik", "penelitian", "perilaku", "wawancara_teknis"]},
        {"name": "Pengajaran", "subdomains": ["sokratik", "pendampingan", "bimbingan", "tanya_jawab_kuliah", "umpan_balik", "panduan_belajar"]},
        {"name": "Bermain Peran", "subdomains": ["tokoh_sejarah", "profesional", "layanan_pelanggan", "terapeutik", "negosiasi", "kolaboratif"]},
    ],
}
