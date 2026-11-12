# TaskGen-ID

TaskGen-ID adalah generator dataset pesan/pertanyaan sintetis berbahasa Indonesia untuk kebutuhan Supervised Fine-Tuning (SFT).

## Versi Python

Engine menggunakan **Python standard library saja**. Tidak membutuhkan Cargo, Rust, `pip install`, atau pustaka pihak ketiga. Cocok dijalankan langsung di Termux.

### Menjalankan di Termux

```bash
pkg update
pkg install python git
git clone https://github.com/IND-NV/taskgen-id.git
cd taskgen-id
python taskgen-id.py
```

Saat dijalankan tanpa argumen, program akan meminta satu atau beberapa API key Gemini, mengambil daftar model, lalu meminta pilihan model, jumlah data, worker, batch, kategori, dan nama berkas keluaran. Tingkat kesulitan, domain, dan subdomain dipilih otomatis secara acak sebagai konteks generasi; pengguna tidak perlu memilih level. API key hanya disimpan di memori selama sesi aktif dan tidak ditulis ke berkas.

Jika satu key terkena batas kuota atau pembatasan permintaan, program mencoba key lain yang dimasukkan pada sesi yang sama. Data yang sudah berhasil dibuat tetap tersimpan.

### Contoh CLI

```bash
python taskgen-id.py --count 100 --workers 1 --batch-size 2 --output output.json
python taskgen-id.py -c 50 -w 2 --categories math,coding
python taskgen-id.py --api-key KEY_PERTAMA --api-key KEY_KEDUA
python taskgen-id.py --help
```

## Struktur proyek

```text
taskgen-id/
├── taskgen-id.py
├── providers/
│   ├── registry.py
│   └── gemini.py
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

## Menambah penyedia API

Setiap penyedia ditempatkan pada berkas terpisah di `providers/`. Saat ini hanya Gemini yang didaftarkan di `providers/registry.py`. Penyedia baru nantinya dapat ditambahkan sebagai modul tersendiri, misalnya `providers/openrouter.py`, tanpa memindahkan logika penyusunan dataset dari engine. Semua penyedia baru perlu menyediakan antarmuka daftar model dan Chat Completions yang sama.

## Menambah kategori

Buat modul baru di `categories/` dengan variabel `CATEGORY`, lalu daftarkan di `categories/registry.py`. ID internal seperti `math` dan `coding` sengaja dipertahankan agar konfigurasi dan CLI tetap stabil. Nama kategori, domain, dan subdomain yang masuk ke dataset menggunakan bahasa Indonesia.

## Bahasa keluaran dan metadata

Utamakan bahasa Indonesia yang alami untuk isi pertanyaan dan metadata kategori/domain/subdomain. Istilah, frasa, nama produk, bahasa pemrograman, protokol, singkatan baku, atau ungkapan bahasa Inggris maupun bahasa lain boleh digunakan jika sesuai konteks; tidak perlu memaksakan terjemahan.

## Fitur

- Gemini melalui endpoint OpenAI-compatible.
- Pengambilan daftar model dan pemilihan model saat mulai.
- Beberapa API key dalam satu sesi, dengan pergantian otomatis saat terkena 401, 403, atau 429.
- API key tidak disimpan ke konfigurasi maupun hasil dataset.
- Batch kecil dan worker yang dapat diatur; gunakan 1 worker dan batch 2 di ponsel.
- Penyimpanan JSON atomik setelah setiap batch berhasil.
- ID berurutan enam digit.
- Distribusi kategori dapat diatur; domain, subdomain, dan tingkat kesulitan dipilih otomatis secara acak.
- Prompt sistem dapat diganti dari berkas.

## Format keluaran

JSON array dengan empat field: `question`, `language`, `main_category`, dan `id`. Domain, subdomain, serta tingkat kesulitan hanya digunakan sebagai konteks internal untuk mengarahkan variasi generasi dan tidak disimpan di dataset. Nilai `main_category` menggunakan label Indonesia.

## Catatan

- Gunakan nama berkas keluaran baru jika ingin memulai dataset terpisah.
- Engine membaca file JSON lama dan melanjutkan ID dari record yang sudah ada.
- Notebook Colab lama masih dalam proses penyesuaian ke engine Python; jalankan CLI Python untuk versi migrasi ini.
