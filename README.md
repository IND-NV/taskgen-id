# TaskGen Indonesia — Gemini API

TaskGen Indonesia adalah generator tugas/pertanyaan untuk membangun dataset bergaya supervised fine-tuning (SFT). Implementasi generator ditulis dalam Rust dan menggunakan Google Gemini API melalui REST native. Notebook Google Colab menyediakan UI untuk menghasilkan data dan menyimpan satu dataset gabungan ke Google Drive.

> **Catatan keamanan output:** CLI kini menulis ringkasan generasi ke `DATASET_README.md` di folder induk `--output`, bukan ke README project. Lokasinya dapat diubah dengan `--readme-output`. Hindari memilih path yang sama dengan file output dataset.

## Fitur

- Menggunakan Gemini API native REST (`generateContent`), tanpa OpenAI API atau Python SDK `google-genai`.
- API key dibaca dari `GEMINI_API_KEY` atau argumen CLI yang tersedia.
- Model dapat dipilih saat menjalankan CLI; notebook mengambil daftar model yang mendukung `generateContent` dari API.
- System prompt berbahasa Indonesia dengan penyesuaian nada/konteks dan empat label kompleksitas: `easy`, `medium`, `hard`, `expert`.
- Enam kategori: matematika, pemrograman, sains, ilmu komputer, kreativitas/penulisan, dan percakapan.
- Bobot kategori dan label kesulitan dapat dikonfigurasi; label didasarkan pada kompleksitas penalaran, bukan nomor.
- Permintaan batch dan worker paralel.
- Retry dengan jeda bertahap untuk HTTP 429 dan timeout, serta penghentian ketika terdeteksi masalah billing.
- Output CLI berupa JSONL, satu task per baris; notebook menggabungkan hasil ke JSON array di Google Drive.
- Opsi deduplikasi; notebook melakukan deduplikasi teks prompt pada dataset gabungan.
- Statistik token dan README ringkasan generasi untuk output CLI.

## Struktur repository

```text
taskgen-id/
├── Cargo.toml
├── Cargo.lock
├── README.md
├── CONTEXT_FOR_AI.md
├── src/
│   └── main.rs
└── taskgen_id.ipynb
```

## Menjalankan di Google Colab (disarankan)

1. Buka notebook [`taskgen_id.ipynb`](taskgen_id.ipynb) di GitHub.
2. Pilih **Open in Colab** atau unggah notebook ke Google Colab.
3. Jalankan sel notebook. Notebook akan memasang/menghubungkan Google Drive, mengunduh branch `main`, dan membangun binary Rust.
4. Simpan API key sebagai Colab Secret bernama `GEMINI_API_KEY`. Jika Secret tidak tersedia, notebook meminta API key melalui input tersembunyi.
5. Pilih model, jumlah tugas, kategori, tingkat kesulitan, dan jumlah worker; lalu tekan **Generate**.
6. Dataset gabungan disimpan ke `MyDrive/TaskGen-Indonesia/task_id.json`.

Notebook menyimpan delapan field dalam JSON array: `id`, `generated_date`, `domain`, `subdomain`, `difficulty`, `language`, `prompt`, dan `model`. CLI menggunakan JSONL dengan skema yang sama. Notebook menggunakan temperatur `1.0` dan secara default mengaktifkan deduplikasi prompt.

Notebook mengkloning branch `main` dan membangun kode Rust dari repository, jadi perubahan di branch tersebut akan dipakai saat notebook dijalankan kembali. Runtime Colab bersifat sementara; simpan data penting ke Drive.

## Menjalankan CLI di Linux

Pastikan Rust/Cargo tersedia. Jalankan dari direktori kerja terpisah, dan jangan gunakan root repository sebagai direktori output README sampai perilaku penulisan README diperbaiki.

```bash
git clone https://github.com/IND-NV/taskgen-id.git
cd taskgen-id
cargo build --release

export GEMINI_API_KEY="API_KEY_MILIKMU"
mkdir -p generated

./target/release/taskgen \
  --count 100 \
  --model gemini-3.5-flash-lite \
  --distribution "math=0.5,coding=0.5" \
  --output generated/output.jsonl \
  --workers 2
```

Contoh hanya matematika dengan tingkat kesulitan `hard`:

```bash
./target/release/taskgen \
  --count 50 \
  --model gemini-3.5-flash-lite \
  --distribution "math=1.0" \
  --difficulty "hard=1.0" \
  --output generated/matematika_level7.jsonl \
  --workers 2
```

Pastikan direktori yang diberikan ke `--output` sudah ada. Ringkasan generasi ditulis terpisah sebagai `DATASET_README.md`; kamu juga bisa menentukan lokasi dengan `--readme-output generated/summary.md`.

## Opsi CLI utama

| Opsi | Default | Keterangan |
|---|---:|---|
| `--count`, `-c` | `250` | Jumlah tugas yang ditargetkan |
| `--model`, `-m` | `gemini-3.5-flash-lite` | ID model Gemini |
| `--distribution` | Distribusi bawaan | Bobot kategori; total bobot harus mendekati 1.0 |
| `--difficulty` | Distribusi bawaan | Bobot label `easy`, `medium`, `hard`, `expert`; total bobot harus mendekati 1.0 |
| `--workers`, `-w` | `5` | Batas batch yang diproses bersamaan |
| `--output`, `-o` | `output.jsonl` | Lokasi output JSONL |
| `--temperature`, `-t` | `1.0` | Variasi generasi |
| `--append` | Mati | Tambahkan output ke file yang sudah ada |
| `--dedup` | Mati | Deduplikasi exact dan kemiripan trigram setelah generasi |
| `--dedup-threshold` | `0.6` | Ambang kemiripan deduplikasi |
| `--system-prompt` | Prompt bawaan | Mengganti system prompt |
| `--keyfile` | Tidak digunakan | File berisi API key, satu key per baris |
| `--proxies` | Tidak digunakan | File daftar proxy |
| `--input-price`, `--output-price` | Tidak digunakan | Harga per satu juta token untuk estimasi biaya |
| `--budget` | Tidak digunakan | Membutuhkan kedua harga token; batch dijalankan serial saat budget aktif, tetapi satu batch masih dapat melampaui batas |
| `--readme-output` | `DATASET_README.md` di folder output | Lokasi ringkasan generasi; tidak lagi menimpa README project secara default |

### ID kategori

- `math`: Matematika
- `coding`: Pemrograman
- `science`: Sains
- `cs`: Ilmu komputer
- `creative`: Kreativitas dan penulisan
- `conversation`: Percakapan

Contoh memilih satu kategori: `--distribution "science=1.0"`. Untuk satu label: `--difficulty "medium=1.0"`. Contoh bobot khusus: `--difficulty "easy=0.15,medium=0.45,hard=0.25,expert=0.15"`.

## Format output

### CLI: JSONL

Satu baris untuk setiap task:

```json
{"id":"question-000001","generated_date":"2026-10-17","domain":"Matematika::Aljabar","subdomain":"linear_equations","difficulty":"medium","language":"id","prompt":"Bagaimana cara ...?","model":"gemini-3.5-flash-lite"}
```

Urutan field kanonis: `id`, `generated_date`, `domain`, `subdomain`, `difficulty`, `language`, `prompt`, `model`. ID berbentuk `question-000001` dan berurutan; mode append melanjutkan nomor tertinggi yang ada. `generated_date` menggunakan format `YYYY-MM-DD`; tanggal historis yang tidak diketahui tetap `null`. Data lama dipertahankan dan tingkat kesulitan numerik dipetakan: 1–3 ke `easy`, 4–6 ke `medium`, 7–8 ke `hard`, 9–10 ke `expert`.

### Notebook: JSON array

Notebook menggabungkan hasil ke `MyDrive/TaskGen-Indonesia/task_id.json` sebagai JSON array dengan delapan field kanonis yang sama. Format kontainer berbeda dari JSONL CLI, tetapi skema record konsisten.

## Rate limit, model, dan kualitas data

- Program mencoba ulang permintaan ketika menerima HTTP 429 atau timeout, sampai batas percobaan yang ditentukan kode.
- Program tidak berpindah model otomatis. Pilih model lain secara eksplisit untuk run berikutnya jika model yang dipilih tidak tersedia atau kuotanya habis.
- Mulai dengan 10–20 tugas dan `--workers 1` atau `--workers 2` sebelum memperbesar run.
- Ketersediaan model, kuota, dan biaya mengikuti akun Google AI Studio/API yang digunakan.
- Periksa sampel output sebelum digunakan untuk pelatihan. Instruksi bahasa Indonesia bukan jaminan bahwa setiap keluaran model sempurna atau faktual.

## Keamanan

- Jangan commit `GEMINI_API_KEY`, file key, atau kredensial ke GitHub.
- Gunakan Colab Secrets atau environment variable.
- Dataset disimpan ke Google Drive oleh notebook; jangan commit dataset pribadi atau besar ke repository tanpa alasan yang jelas.

## Catatan pengembangan

Lihat [`CONTEXT_FOR_AI.md`](CONTEXT_FOR_AI.md) untuk ringkasan arsitektur, perilaku penting, risiko yang sudah ditemukan, dan daftar pekerjaan lanjutan agar konteks pengembangan tidak hanya bergantung pada riwayat percakapan.
