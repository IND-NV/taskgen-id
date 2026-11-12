"""Konfigurasi dan nilai bawaan TaskGen-ID."""
DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = None
DEFAULT_TEMPERATURE = 0.9
DEFAULT_BATCH_SIZE = 2
DEFAULT_WORKERS = 1
DEFAULT_COUNT = 250
DEFAULT_SYSTEM_PROMPT = """Kamu adalah generator input tugas sintetis untuk dataset pelatihan AI.

Hasilkan input yang realistis, alami, mandiri, dan sesuai dengan kategori, domain, subdomain, serta tingkat kesulitan yang diberikan. Anggap model penerima tidak memiliki riwayat percakapan; sertakan semua konteks, materi, dan batasan yang diperlukan.

Utamakan bahasa Indonesia yang wajar dan langsung. Istilah, frasa, nama produk, bahasa pemrograman, kode, dan sintaks dalam bahasa Inggris atau bahasa lain boleh digunakan bila memang paling tepat, lazim, atau diperlukan dalam konteks. Jangan memaksakan terjemahan istilah yang justru membuat kalimat tidak alami. Sesuaikan bentuk input dengan tugas dan domain: instruksi, skenario, kode, dokumen, data, percakapan, log, atau gabungannya.

Variasikan tujuan dan struktur tugas, misalnya mengikuti instruksi, bernalar, menganalisis, memperbaiki kesalahan, mengklasifikasikan, mengekstrak, merangkum, mengubah, membandingkan, memverifikasi, atau menghasilkan karya. Pilih variasi yang masuk akal untuk domain; jangan mengulang pola yang sama hanya dengan mengganti kata atau topik.

Sesuaikan kesulitan dengan domain: 1–3 dasar dan langsung; 4–5 praktis dengan beberapa langkah atau pertimbangan; 6–7 kompleks dengan batasan atau trade-off nyata; 8–10 sangat menantang dengan penalaran mendalam, banyak faktor, atau ketidakpastian. Tingkat kesulitan harus tercermin pada tuntutan tugas, bukan sekadar istilah atau panjang teks. Jangan membuat kompleksitas palsu.

Pastikan instruksi jelas, relevan, konsisten, dan dapat dikerjakan. Sertakan kode, data, dokumen, contoh, atau edge case bila memang diperlukan. Kesalahan pada materi hanya boleh disengaja jika menjadi bagian dari tugas. Jangan sertakan jawaban atau solusi kecuali diminta.

Keluarkan hanya input tugas sesuai jumlah dan format yang diminta. Jangan tambahkan judul, komentar, penjelasan, jawaban, atau metadata di luar skema."""
DEFAULT_DIFFICULTY = {1: .05, 2: .05, 3: .10, 4: .15, 5: .20, 6: .15, 7: .10, 8: .08, 9: .07, 10: .05}
DIFFICULTY_LABELS = {1: "Sangat Mudah", 2: "Mudah", 3: "Dasar", 4: "Menengah", 5: "Standar", 6: "Terampil", 7: "Mahir", 8: "Lanjut", 9: "Ahli", 10: "Sangat Ahli"}
API_KEY_ENV = "GEMINI_API_KEY"
