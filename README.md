# TaskGen Indonesia — Gemini API

TaskGen adalah generator tugas/pertanyaan untuk membuat dataset bergaya SFT. Versi ini disesuaikan agar **menggunakan Google Gemini API saja** dan mengarahkan semua tugas yang dihasilkan ke **bahasa Indonesia**.

## Fitur

- Menggunakan Gemini API native REST (`generateContent`), bukan OpenAI API dan bukan `google-genai` Python SDK.
- API key dibaca dari variabel lingkungan `GEMINI_API_KEY`.
- Nama model dapat dipilih saat menjalankan program dengan `--model`.
- System prompt diterjemahkan ke bahasa Indonesia dengan logika tingkat kesulitan dan gaya pertanyaan asli tetap dipertahankan.
- Kategori bawaan tetap dipertahankan: matematika, pemrograman, sains, ilmu komputer, kreativitas/penulisan, dan percakapan.
- Tingkat kesulitan 1–10 dengan distribusi bawaan atau distribusi yang dapat diatur.
- Output JSONL berisi prompt, kategori/domain, subtopik, tingkat kesulitan, bahasa (`id`), model, dan temperatur.
- Penyimpanan bertahap ke file; hasil yang berhasil dibuat tetap ditulis meskipun tugas berikutnya gagal.
- Retry dengan jeda bertahap untuk rate limit (`429`) dan timeout.
- Deduplikasi opsional.
- Notebook Google Colab untuk mengatur jumlah, kategori, level, model, dan folder Google Drive.

## Kategori bawaan

| Pilihan di Colab | ID internal | Isi |
|---|---|---|
| Matematika | `math` | Aljabar, kalkulus, probabilitas, statistika, geometri, dan lainnya |
| Pemrograman | `coding` | Bahasa pemrograman, pengembangan web, basis data, dan lainnya |
| Sains | `science` | Fisika, kimia, biologi, ilmu kebumian, astronomi |
| Ilmu komputer | `cs` | Algoritma, struktur data, sistem operasi, jaringan, machine learning, keamanan siber, dan lainnya |
| Kreativitas dan penulisan | `creative` | Fiksi, puisi, skenario, blogging, dan lainnya |
| Percakapan | `conversation` | Debat, saran, wawancara, pengajaran, permainan peran |

Semua kategori dan subtopik dari proyek asal dipertahankan. Kategori yang dipilih akan menentukan kumpulan subtopik yang dipilih program secara acak. Label kategori/domain yang ditampilkan dalam instruksi dan metadata telah diterjemahkan bila sesuai; nama teknis seperti Python, Rust, SQL, dan istilah teknis dipertahankan.

## Menjalankan di Google Colab (disarankan)

1. Push repositori ini ke GitHub milikmu.
2. Buka file `TaskGen_Indonesia_Colab.ipynb` di GitHub, lalu pilih **Open in Colab** (atau unggah notebook ke Colab).
3. Jalankan sel secara berurutan.
4. Masukkan URL repositori GitHub saat diminta.
5. Simpan API key sebagai Colab Secret bernama `GEMINI_API_KEY` (disarankan), atau masukkan saat diminta. Jangan commit API key ke GitHub.
6. Pilih jumlah tugas, kategori, tingkat kesulitan, dan model Gemini.
7. Notebook akan membangun program Rust dan menyimpan hasil di `MyDrive/TaskGen-Indonesia/`.

Notebook mencoba mengambil daftar model yang tersedia melalui Gemini API. Kamu bisa memilih model dari daftar atau mengetik ID model sendiri. Model yang muncul belum tentu semuanya punya kuota gratis; ketersediaan dan limit bergantung pada akun Google AI Studio dan model.

## Menjalankan langsung di Linux

Pastikan Rust/Cargo tersedia, lalu:

```bash
cargo build --release
export GEMINI_API_KEY="API_KEY_MILIKMU"

# Contoh: 100 tugas, model Flash-Lite, kategori matematika + pemrograman, level campuran
./target/release/taskgen \
  --count 100 \
  --model gemini-3.5-flash-lite \
  --distribution "math=0.5,coding=0.5" \
  --output output.jsonl \
  --workers 2
```

Contoh hanya matematika dan tingkat kesulitan 7:

```bash
./target/release/taskgen \
  --count 50 \
  --model gemini-3.5-flash-lite \
  --distribution "math=1.0" \
  --difficulty "7=1.0" \
  --output matematika_level7.jsonl \
  --workers 2
```

## Opsi utama

| Opsi | Default | Keterangan |
|---|---:|---|
| `--count`, `-c` | `250` | Jumlah tugas yang ditargetkan |
| `--model`, `-m` | `gemini-3.5-flash-lite` | ID model Gemini; bisa diganti setiap run |
| `--distribution` | distribusi bawaan | Bobot kategori; total bobot harus sekitar 1.0 |
| `--difficulty` | distribusi bawaan | Bobot level 1–10; total bobot harus sekitar 1.0 |
| `--workers`, `-w` | `5` | Permintaan paralel; untuk kuota gratis disarankan mulai dari 1–2 |
| `--output`, `-o` | `output.jsonl` | Lokasi file hasil |
| `--temperature`, `-t` | `0.9` | Variasi generasi |
| `--dedup` | mati | Jalankan deduplikasi setelah generasi |
| `--append` | mati | Tambahkan ke file yang sudah ada |

### ID kategori untuk `--distribution`

- `math`: Matematika
- `coding`: Pemrograman
- `science`: Sains
- `cs`: Ilmu komputer
- `creative`: Kreativitas dan penulisan
- `conversation`: Percakapan

Untuk memilih hanya satu kategori, gunakan bobot `1.0`, misalnya `--distribution "science=1.0"`. Untuk level tertentu, gunakan `--difficulty "4=1.0"`. Untuk level campuran, hilangkan opsi `--difficulty` agar distribusi bawaan digunakan.

## Rate limit dan model

Program menggunakan model yang dipilih untuk seluruh run. Jika menerima `429`, program menunggu dengan jeda bertahap dan mencoba ulang hingga batas percobaan. **Program tidak berpindah model secara otomatis**, sehingga metadata dataset tetap konsisten dan penggunaan model tidak berubah diam-diam. Jika kuota model habis, pilih model lain saat run berikutnya. Mengganti model tidak menjamin kuota tambahan.

Untuk mengurangi rate limit di akun gratis, mulai dari `--workers 1` atau `--workers 2`. Jangan meminta ribuan tugas sekaligus sebelum menguji 10–20 tugas. Penggunaan token bergantung pada panjang prompt dan output.

## Output JSONL

Satu tugas disimpan per baris, misalnya:

```json
{"prompt":"Bagaimana cara ...?","domain":"Matematika::Aljabar","subdomain":"linear_equations","difficulty":4,"language":"id","taskgen_model":"gemini-3.5-flash-lite","temperature":0.9}
```

Catatan: isi prompt diarahkan ke bahasa Indonesia, tetapi istilah teknis, nama produk, bahasa pemrograman, atau istilah yang lebih tepat dipertahankan dalam bahasa aslinya. Validasi hasil sampel tetap disarankan.

## Keamanan

- Jangan pernah commit `GEMINI_API_KEY` ke GitHub.
- Di Colab, gunakan **Secrets** dengan nama `GEMINI_API_KEY`.
- Hasil dataset disimpan di Google Drive, bukan di repositori kode.
- Colab menggunakan runtime sementara; file hasil yang sudah tersimpan ke Drive akan tetap ada setelah runtime berhenti.
