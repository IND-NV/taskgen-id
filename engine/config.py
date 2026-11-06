"""Konfigurasi dan nilai default TaskGen-ID."""
import os

DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_TEMPERATURE = 0.9
DEFAULT_BATCH_SIZE = 2
DEFAULT_WORKERS = 1
DEFAULT_COUNT = 250
DEFAULT_SYSTEM_PROMPT = """Kamu adalah generator pesan pengguna sintetis untuk membangun dataset Supervised Fine-Tuning (SFT) AI serbaguna berbahasa Indonesia.

Setiap pesan harus realistis, kontekstual, memiliki tujuan jelas, informatif, koheren, natural, tidak bertele-tele, dan bervariasi. Sertakan latar belakang, situasi, tujuan, kendala, atau pengalaman yang relevan. Hindari pertanyaan generik tanpa konteks.

Sesuaikan detail dengan jenis tugas: troubleshooting (perangkat, gejala, tindakan yang dicoba), coding (tujuan, lingkungan, kode/error), brainstorming (ide, target, batasan), planning (tujuan, waktu, sumber daya), learning (tingkat pemahaman dan kesulitan), writing (jenis tulisan, audiens, gaya), decision making (pilihan dan pertimbangan), conversation (hubungan dan tujuan interaksi), creative (tema, suasana, karakter), dan general knowledge (rasa ingin tahu atau kebutuhan praktis).

Tingkat kesulitan: 1-3 basic; 4-5 intermediate/practitioner; 6-7 advanced/expert; 8-10 cutting-edge/polymath. Level mengukur kompleksitas tugas, bukan panjang pesan. Untuk level 6 ke atas, sertakan trade-off atau tantangan nyata yang relevan, bukan konflik palsu.

Gunakan bahasa Indonesia yang natural, santai, dan manusiawi. Hasilkan tepat satu pesan pengguna per spesifikasi. Hanya isi pesan pengguna; jangan menjawab pertanyaan, menambah metadata, judul, komentar, atau menyebut bahwa pesan dibuat AI."""
DEFAULT_DIFFICULTY = {1: .05, 2: .05, 3: .10, 4: .15, 5: .20, 6: .15, 7: .10, 8: .08, 9: .07, 10: .05}
DIFFICULTY_LABELS = {1:"Very Easy (child-level)",2:"Easy (elementary)",3:"Basic (middle school)",4:"Intermediate (high school)",5:"Standard (undergraduate intro)",6:"Skilled (undergraduate advanced)",7:"Proficient (graduate level)",8:"Advanced (professional/researcher)",9:"Expert (top specialist)",10:"Polymath (1-in-a-million genius)"}
API_KEY_ENV = "GEMINI_API_KEY"
