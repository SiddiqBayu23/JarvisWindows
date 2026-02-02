# JARVIS Windows Plus - Install Guide

## 1. Install Python
- Download Python 3.11 dari https://www.python.org/downloads/
- Centang "Add to PATH" saat instalasi

## 2. Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Konfigurasi API Key
- Buka file `.env`
- Isi dengan OpenAI API key kamu

## 4. Jalankan manual (tes)
```bash
python backend/jarvis.py
```

## 5. Auto-start dengan Task Scheduler
- Buka Task Scheduler
- Import `Jarvis_Autostart.xml`
- JARVIS akan otomatis jalan setiap login
