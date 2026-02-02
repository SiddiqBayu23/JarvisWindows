# JarvisWindows 🤖💻

**JarvisWindows** adalah asisten virtual pribadi berbasis Python yang dirancang khusus untuk sistem operasi Windows. Proyek ini menggabungkan kemampuan otomatisasi sistem dengan fitur keamanan biometrik sederhana menggunakan pengenalan wajah.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
![Status](https://img.shields.io/badge/Status-Active-success)

## ✨ Fitur Utama

* **Pengenalan Wajah (Face Recognition):** Sistem keamanan cerdas yang memverifikasi identitas pengguna menggunakan folder `known_faces` sebelum memberikan akses atau menjalankan perintah.
* **Integrasi Windows:** Dirancang untuk berjalan mulus di lingkungan Windows.
* **Auto-Start System:** Dilengkapi dengan konfigurasi XML (`Jarvis_Autostart.xml`) untuk menjalankan asisten secara otomatis saat Windows dinyalakan menggunakan Task Scheduler.
* **Interaksi Suara:** (Berdasarkan adanya file audio) Mendukung respon audio/suara untuk interaksi yang lebih natural.
* **Backend Modular:** Logika program terpisah di dalam folder `backend` untuk pengelolaan kode yang lebih rapi.

## 📂 Struktur Repositori

```text
JarvisWindows/
├── backend/               # Kode sumber utama dan logika program
├── known_faces/           # Folder untuk menyimpan data wajah pengguna yang dikenali
├── .env                   # File konfigurasi untuk variabel lingkungan (API Keys, dll)
├── INSTALL.md             # Panduan instalasi mendetail
├── Jarvis_Autostart.xml   # File konfigurasi untuk Windows Task Scheduler
├── requirements.txt       # Daftar dependensi Python
└── temp.mp3               # File cache audio sementara
