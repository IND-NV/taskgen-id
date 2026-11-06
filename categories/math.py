"""Kategori matematika TaskGen-ID."""

CATEGORY = {
    "id": "math",
    "name": "Matematika",
    "domains": [
        {"name": "Aljabar", "subdomains": ["persamaan_linear", "polinomial", "pertidaksamaan", "matriks", "aljabar_abstrak"]},
        {"name": "Kalkulus", "subdomains": ["turunan", "integral", "limit", "deret", "kalkulus_multivariabel"]},
        {"name": "Probabilitas", "subdomains": ["bayes", "distribusi", "kombinatorika", "proses_stokastik", "rantai_markov"]},
        {"name": "Statistika", "subdomains": ["pengujian_hipotesis", "regresi", "anova", "statistika_deskriptif", "statistika_bayes"]},
        {"name": "Geometri", "subdomains": ["euclidean", "analitik", "diferensial", "topologi", "trigonometri"]},
        {"name": "Teori Bilangan", "subdomains": ["bilangan_prima", "aritmetika_modular", "persamaan_diofantin", "kriptografi", "teori_bilangan_aljabar"]},
        {"name": "Matematika Diskrit", "subdomains": ["teori_graf", "kombinatorika", "logika", "teori_himpunan", "relasi_berulang"]},
        {"name": "Aljabar Linear", "subdomains": ["ruang_vektor", "nilai_eigen", "transformasi", "hasil_kali_dalam", "dekomposisi"]},
    ],
}
