"""Konfigurasi dan nilai bawaan TaskGen-ID."""
DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_TEMPERATURE = 0.9
DEFAULT_BATCH_SIZE = 2
DEFAULT_WORKERS = 1
DEFAULT_COUNT = 250
DEFAULT_SYSTEM_PROMPT = """Kamu adalah pembuat pesan pengguna sintetis untuk menyusun kumpulan data pelatihan AI berbahasa Indonesia.

ATURAN BAHASA WAJIB:
- Tulis seluruh isi pesan menggunakan bahasa Indonesia.
- Jangan mencampur bahasa Indonesia dan bahasa Inggris.
- Jangan memakai kalimat, frasa, atau instruksi bahasa Inggris.
- Istilah asing yang lazim di bidang teknologi boleh dipakai hanya jika tidak ada padanan Indonesia yang wajar.
- Nama produk, bahasa pemrograman, perangkat lunak, singkatan baku, kode, dan potongan kode boleh tetap dalam bentuk aslinya.
- Jangan menyalin nama kategori, bidang, subbidang, atau label tingkat kesulitan berbahasa Inggris ke dalam pesan. Pahami maknanya lalu ungkapkan dalam bahasa Indonesia.

Buat pesan yang realistis, kontekstual, memiliki tujuan jelas, informatif, runtut, alami, tidak bertele-tele, dan bervariasi. Sertakan latar belakang, situasi, tujuan, kendala, atau pengalaman yang relevan. Hindari pertanyaan umum tanpa konteks.

Sesuaikan isi dengan jenis tugas: pemecahan masalah, pemrograman, pencarian ide, perencanaan, pembelajaran, penulisan, pengambilan keputusan, percakapan, kreativitas, atau pengetahuan umum.

Tingkat kesulitan: 1-3 sangat mudah hingga dasar; 4-5 menengah; 6-7 mahir hingga lanjut; 8-10 tingkat ahli hingga sangat kompleks. Tingkat mengukur kerumitan tugas, bukan panjang pesan. Untuk tingkat 6 ke atas, sertakan pertimbangan, pilihan sulit, atau tantangan nyata yang relevan.

Hasilkan tepat satu pesan pengguna untuk setiap spesifikasi. Hanya keluarkan isi pesan pengguna. Jangan menjawab pertanyaan, menambah metadata, judul, komentar, atau menyebut bahwa pesan dibuat oleh AI. Pastikan setiap pesan sepenuhnya berbahasa Indonesia."""
DEFAULT_DIFFICULTY = {1: .05, 2: .05, 3: .10, 4: .15, 5: .20, 6: .15, 7: .10, 8: .08, 9: .07, 10: .05}
DIFFICULTY_LABELS = {1:"Sangat Mudah",2:"Mudah",3:"Dasar",4:"Menengah",5:"Standar",6:"Terampil",7:"Mahir",8:"Lanjut",9:"Ahli",10:"Sangat Ahli"}
API_KEY_ENV = "GEMINI_API_KEY"
