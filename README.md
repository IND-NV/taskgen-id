# TaskGen-ID

TaskGen-ID adalah generator dataset pesan/pertanyaan sintetis berbahasa Indonesia untuk kebutuhan Supervised Fine-Tuning (SFT).

## Versi Python (pengganti Rust)

Engine sekarang menggunakan **Python standard library saja**. Tidak membutuhkan Cargo, Rust, `pip install`, `requests`, atau library pihak ketiga. Komunikasi API menggunakan `urllib`.

### Menjalankan di Termux

```bash
pkg update
pkg install python git
git clone https://github.com/IND-NV/taskgen-id.git
cd taskgen-id
python taskgen-id.py
```

Saat dijalankan tanpa argumen, CLI akan menanyakan jumlah data, worker, batch, kategori, dan nama file output. Default aman untuk ponsel: 10 data, 1 worker, batch 2.

Atur API key melalui environment variable:

```bash
export GEMINI_API_KEY="API_KEY_KAMU"
python taskgen-id.py
```

### Contoh CLI

```bash
python taskgen-id.py --count 100 --workers 1 --batch-size 2 --output output.json
python taskgen-id.py -c 50 -w 2 --categories math,coding
python taskgen-id.py --help
```

## Struktur proyek

```text
taskgen-id/
├── taskgen-id.py
├── engine/
│   ├── api.py
│   ├── config.py
│   ├── generator.py
│   ├── sampler.py
│   └── storage.py
├── categories/
│   ├── registry.py
│   ├── math.py
│   ├── coding.py
│   ├── science.py
│   ├── cs.py
│   ├── creative.py
│   └── conversation.py
└── output.json
```

Untuk menambah kategori, buat modul baru di `categories/` dengan variabel `CATEGORY`, lalu daftarkan di `categories/registry.py`.

## Bahasa keluaran

Isi pertanyaan yang dihasilkan diwajibkan menggunakan bahasa Indonesia, bukan campuran Indonesia-Inggris. Istilah teknis, nama produk, nama perangkat lunak, dan potongan kode boleh dipertahankan jika memang perlu. Nama kategori/domain dan nama kolom JSON tetap menjadi penanda internal agar format data stabil.

## Fitur engine

- Endpoint kompatibel OpenAI Chat Completions (default Gemini).
- Batch hingga 2 prompt per request secara default.
- Worker paralel yang bisa diatur; gunakan 1–2 di Termux.
- Retry untuk rate limit dan gangguan sementara.
- Penyimpanan JSON atomik setiap record selesai.
- ID berurutan enam digit.
- Distribusi kategori dan tingkat kesulitan yang dapat diatur.
- Prompt sistem dapat diganti dari file.
- API key tidak ditulis ke output.

## Format output

Output berupa JSON array dengan tujuh field: `question`, `language`, `main_category`, `domain`, `subdomain`, `difficulty_level`, dan `id`.

## Catatan

- Gunakan output filename baru jika ingin memulai dataset terpisah.
- Engine membaca file JSON lama dan melanjutkan ID dari record yang sudah ada.
- Notebook Colab lama masih dalam proses penyesuaian ke engine Python; jalankan CLI Python untuk versi migrasi ini.
