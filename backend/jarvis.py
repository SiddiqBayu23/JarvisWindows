import os
import sys
import cv2
import numpy as np
import speech_recognition as sr
import keyboard
import pystray
from PIL import Image, ImageDraw
import threading
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess
from gtts import gTTS
import pygame
import pywhatkit
from datetime import datetime, timedelta
import locale
import requests
import platform
import wikipedia
import time
import random
import re

# === LOCALE & API CONFIG ===
try:
    locale.setlocale(locale.LC_TIME, "id_ID.utf8")
except:
    pass

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# === GLOBAL STATE ===
is_muted = False
alarms = []

# === TOGGLE MUTE ===
def toggle_mute():
    global is_muted
    is_muted = not is_muted
    print("🔇 JARVIS dimute" if is_muted else "🔊 JARVIS aktif")

keyboard.add_hotkey("ctrl+shift+m", toggle_mute)

# === TRAY ICON ===
def create_image():
    img = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(img)
    d.rectangle((16, 16, 48, 48), fill="white")
    return img

def on_quit(icon, item):
    icon.stop()
    print("Jarvis dihentikan dari tray icon.")
    sys.exit(0)

def on_mute(icon, item):
    toggle_mute()

icon = pystray.Icon("Jarvis", create_image(), menu=pystray.Menu(
    pystray.MenuItem("Mute/Unmute", on_mute),
    pystray.MenuItem("Exit", on_quit)
))
threading.Thread(target=icon.run, daemon=True).start()

# === AUDIO ENGINE ===
recognizer = sr.Recognizer()
mic = sr.Microphone()
pygame.mixer.init()

def speak(text, style="normal"):
    if text and not is_muted:
        if style=="fun":
            fun_responses = ["Baik, Pak!","Siap, Pak!","Segera dilakukan!","On it, Pak!","Sesuai permintaan!"]
            text = f"{random.choice(fun_responses)} {text}"
        print(f"🔊 Jarvis: {text}")
        temp_path = "temp_audio.mp3"
        try:
            tts = gTTS(text=text, lang="id")
            tts.save(temp_path)
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            os.remove(temp_path)
        except Exception as e:
            print(f"⚠️ Error speak: {e}")

# === GEMINI AI ===
def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# === WEATHER ===
def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "API cuaca belum dikonfigurasi, Pak."
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=id"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("cod") != 200:
            return f"Maaf Pak, saya tidak menemukan info cuaca untuk {city}."
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        return f"Cuaca di {city} {weather} dengan suhu {temp}°C, terasa seperti {feels_like}°C."
    except Exception as e:
        return f"Error mengambil cuaca: {e}"

# === FACE RECOGNITION & OWNER CHECK ===
def face_recognition_login():
    try:
        speak("Memulai sistem pengenalan wajah, silakan lihat ke kamera, Pak.")
        video_capture = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        known_faces_folder = "known_faces"
        images, labels, label_dict = [], [], {}
        current_label = 0
        owner_label = None

        for filename in os.listdir(known_faces_folder):
            if filename.lower().endswith((".jpg",".png")):
                img_path = os.path.join(known_faces_folder, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                faces = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5, minSize=(100,100))
                for (x, y, w, h) in faces:
                    images.append(img[y:y+h, x:x+w])
                    labels.append(current_label)
                    label_dict[current_label] = os.path.splitext(filename)[0]
                    if filename.lower() == "owner.jpg":
                        owner_label = current_label
                    current_label += 1

        if not images:
            speak("Tidak ada wajah dikenal. Tambahkan gambar di folder known_faces.")
            return None

        recognizer.train(images, np.array(labels))
        recognized = False
        owner_recognized = False
        start_time = datetime.now()
        name = ""

        while True:
            ret, frame = video_capture.read()
            if not ret: continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100,100))
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                label, confidence = recognizer.predict(face_roi)
                if confidence < 80:
                    name = label_dict[label]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Selamat datang {name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                    recognized = True
                    if label == owner_label:
                        owner_recognized = True
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Tidak dikenal", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

            cv2.imshow("Jarvis Face Recognition", frame)
            if recognized or (datetime.now() - start_time).seconds > 15: break
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        video_capture.release()
        cv2.destroyAllWindows()
        if recognized:
            if owner_recognized:
                speak("Pemilik dikenali. Kontrol penuh diberikan.", "fun")
            else:
                speak(f"Halo {name}, akses terbatas diberikan.", "fun")
            return owner_recognized
        else:
            speak("Wajah tidak dikenali. Akses ditolak.")
            return None
    except Exception as e:
        print(f"⚠️ Error pengenalan wajah: {e}")
        speak("Terjadi kesalahan saat inisialisasi sistem wajah.")
        return None

# === CONTROL APPS & FILES ===
def open_app(app_name):
    system = platform.system()
    if system == "Windows":
        paths = {"chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 "notepad": "notepad.exe",
                 "vscode": "code",
                 "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe"}
        path = paths.get(app_name.lower())
        if path:
            subprocess.Popen(path)
            speak(f"{app_name} dibuka")
        else:
            try:
                subprocess.Popen(app_name)
                speak(f"{app_name} dibuka")
            except:
                speak(f"{app_name} tidak ditemukan")

def manage_files(cmd):
    if "buat file" in cmd:
        name = cmd.replace("buat file","").strip()
        open(name,"w").close()
        speak(f"File {name} dibuat")
    elif "buat folder" in cmd:
        name = cmd.replace("buat folder","").strip()
        os.makedirs(name, exist_ok=True)
        speak(f"Folder {name} dibuat")
    elif "hapus file" in cmd:
        name = cmd.replace("hapus file","").strip()
        try:
            os.remove(name)
            speak(f"File {name} dihapus")
        except:
            speak(f"File {name} tidak ditemukan")
    elif "hapus folder" in cmd:
        name = cmd.replace("hapus folder","").strip()
        try:
            os.rmdir(name)
            speak(f"Folder {name} dihapus")
        except:
            speak(f"Folder {name} tidak ditemukan atau tidak kosong")

# === SEARCH PERSON AKURAT ===
def extract_name(cmd):
    match = re.search(r"(siapa itu|cari|ceritakan tentang)\s+(.+)", cmd, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return None

def search_person(name):
    if not name:
        speak("Maaf, saya tidak menangkap nama yang dimaksud.")
        return
    name_clean = name.strip()
    try:
        summary = wikipedia.summary(name_clean, sentences=2, auto_suggest=False)
        speak(f"{name_clean} adalah {summary}")
    except wikipedia.DisambiguationError as e:
        options = ', '.join(e.options[:5])
        speak(f"Terdapat beberapa hasil untuk {name_clean}: {options}. Mohon lebih spesifik.")
    except wikipedia.PageError:
        speak(f"Saya tidak menemukan info detail untuk {name_clean}, tapi saya mencarinya di Google.")
        pywhatkit.search(name_clean)
    except Exception as e:
        speak(f"Terjadi error saat mencari {name_clean}: {e}")

# === SET REMINDER / ALARM ===
def set_alarm(time_str,msg="Alarm"):
    try:
        alarm_time = datetime.strptime(time_str,"%H:%M")
        now = datetime.now()
        alarm_time = alarm_time.replace(year=now.year,month=now.month,day=now.day)
        if alarm_time<now:
            alarm_time += timedelta(days=1)
        alarms.append((alarm_time,msg))
        speak(f"Alarm diatur pukul {time_str} untuk {msg}")
    except:
        speak("Format waktu salah. Gunakan HH:MM")

def check_alarms():
    while True:
        now = datetime.now()
        for alarm in alarms:
            if now>=alarm[0]:
                speak(f"Alarm: {alarm[1]}")
                alarms.remove(alarm)
        time.sleep(10)
threading.Thread(target=check_alarms,daemon=True).start()

# === SYSTEM CONTROL ===
def control_system(cmd):
    system = platform.system()
    if system == "Windows":
        if "matikan" in cmd: speak("Mematikan PC"); os.system("shutdown /s /t 5")
        elif "restart" in cmd: speak("Merestart PC"); os.system("shutdown /r /t 5")
        elif "sleep" in cmd: speak("PC tidur"); os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

# === MAIN COMMAND HANDLER ===
def handle_command(command, stop_listening_callback, owner_control=True):
    cmd = command.lower()
    if "berhenti" in cmd or "keluar" in cmd:
        speak("Jarvis berhenti sekarang, Pak.", "fun")
        if stop_listening_callback: stop_listening_callback(wait_for_stop=False)
        sys.exit(0)
    elif "waktu" in cmd:
        speak(f"Sekarang pukul {datetime.now().strftime('%H:%M')}", "fun")
    elif "tanggal" in cmd:
        speak(f"Hari ini {datetime.now().strftime('%A, %d %B %Y')}", "fun")
    elif "hari" in cmd:
        speak(f"Hari ini {datetime.now().strftime('%A')}", "fun")
    elif "cuaca" in cmd:
        city = cmd.split(" di ")[-1].strip() if " di " in cmd else cmd.replace("cuaca","").strip()
        if city: speak(get_weather(city), "fun")
        else: speak("Kota mana yang ingin dicek cuacanya, Pak?", "fun")
    elif "buka" in cmd or "jalankan" in cmd:
        if owner_control:
            open_app(cmd.replace("buka","").replace("jalankan","").strip())
        else:
            speak("Maaf Pak, hanya Owner bisa membuka aplikasi.", "fun")
    elif any(x in cmd for x in ["buat","hapus"]):
        if owner_control:
            manage_files(cmd)
        else:
            speak("Maaf Pak, hanya Owner yang bisa mengubah file/folder.", "fun")
    elif any(x in cmd for x in ["siapa itu","cari","ceritakan tentang"]):
        name = extract_name(cmd)
        search_person(name)
    elif "alarm" in cmd or "ingatkan" in cmd:
        try:
            parts = cmd.split("pada")
            msg = parts[0].replace("alarm","").replace("ingatkan","").strip()
            set_alarm(parts[1].strip(),msg)
        except:
            speak("Format alarm salah. Gunakan: alarm <pesan> pada HH:MM")
    elif "matikan" in cmd or "restart" in cmd or "sleep" in cmd:
        if owner_control:
            speak("Menjalankan perintah sistem, yakin? (ya/tidak)")
            response = input("Konfirmasi perintah (ya/tidak): ").lower()
            if response=="ya": control_system(cmd)
            else: speak("Perintah sistem dibatalkan.", "fun")
        else:
            speak("Maaf Pak, hanya Owner yang bisa kontrol daya sistem.", "fun")
    else:
        answer = ask_gemini(command)
        speak(answer, "fun")

# === LISTENER CALLBACK ===
def background_callback(recognizer, audio):
    try:
        command = recognizer.recognize_google(audio, language="id-ID")
        print(f"🗣️ Anda: {command}")
        handle_command(command, stop_listening, owner_control=is_owner)
    except sr.UnknownValueError:
        speak("Maaf, saya tidak mengerti. Bisa ulangi?")
    except sr.RequestError as e:
        print(f"⚠️ Error: {e}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    is_owner = face_recognition_login()
    if is_owner is not None:
        current_hour = datetime.now().hour
        if current_hour<12: greet="Selamat pagi, Pak!"
        elif current_hour<18: greet="Selamat siang, Pak!"
        else: greet="Selamat sore, Pak!"
        speak(f"{greet} Saya Jarvis. Ada yang bisa saya bantu?", "fun")
        stop_listening = recognizer.listen_in_background(mic, background_callback)
        print("🎧 Jarvis sekarang mendengarkan...")
        while True:
            pass
    else:
        print("Akses ditolak. Menutup sistem...")
        sys.exit(0)
