import cv2
import numpy as np
import colorsys
import joblib
import os
from sklearn.cluster import KMeans

# --- LOAD MODEL (Kalo ada) ---
if os.path.exists('model_fashion_hsv.pkl'):
    ai_model = joblib.load('model_fashion_hsv.pkl')
    MODEL_READY = True
else:
    MODEL_READY = False

# --- 1. DETEKSI DOMINANT COLOR (MATA) ---
def get_dominant_color(image, k=1):
    # Resize biar enteng
    image = cv2.resize(image, (64, 64))
    
    # Crop 50% Tengah (Fokus ke kain, buang background)
    h, w, _ = image.shape
    start_x, end_x = int(w * 0.25), int(w * 0.75)
    start_y, end_y = int(h * 0.25), int(h * 0.75)
    crop = image[start_y:end_y, start_x:end_x]
    
    # Kalo crop gagal, pake gambar full
    if crop.size == 0: crop = image
        
    pixels = crop.reshape((-1, 3))
    
    # Pake KMeans buat cari warna paling dominan
    clt = KMeans(n_clusters=k, n_init=10)
    clt.fit(pixels)
    return clt.cluster_centers_[0].astype(int)

# --- 2. LOGIKA WARNA TOTAL UPGRADE (HSV STANDARD) ---
def get_human_color(R, G, B):
    # Convert RGB (0-255) ke HSV (0-1)
    h, s, v = colorsys.rgb_to_hsv(R/255.0, G/255.0, B/255.0)
    hue_deg = h * 360 # Jadikan derajat (0-360)

    # --- LEVEL 1: CEK ACHROMATIC (GAK BERWARNA) ---
    # Hitam = Gelap banget (V rendah)
    if v < 0.20: return "Hitam (Black)"
    
    # Putih = Terang banget (V tinggi) DAN Pudar (S rendah)
    if v > 0.80 and s < 0.15: return "Putih (White)"
    
    # Abu-abu = Sisa warna pudar lainnya
    if s < 0.15: return "Abu-abu (Gray)"

    # --- LEVEL 2: CEK CHROMATIC (BERWARNA) ---
    # Kalau lolos dari Level 1, berarti ini warna-warni.
    # Kita bagi lingkaran 360 derajat jadi sektor-sektor.
    
    if (hue_deg >= 0 and hue_deg < 15) or (hue_deg >= 345):
        return "Merah (Red)"
    elif 15 <= hue_deg < 45:
        return "Oranye (Orange)"
    elif 45 <= hue_deg < 85:
        return "Kuning (Yellow)"
    elif 85 <= hue_deg < 165:
        return "Hijau (Green)"
    elif 165 <= hue_deg < 195:
        return "Cyan/Tosca"
    elif 195 <= hue_deg < 260:
        return "Biru (Blue)"
    elif 260 <= hue_deg < 315:
        return "Ungu (Purple)"
    elif 315 <= hue_deg < 345:
        return "Pink (Pink)"
        
    return "Warna Tidak Dikenal"

# --- 3. LOGIKA KECOCOKAN (BRAIN) ---
def check_compatibility(top_rgb, bottom_rgb, nama_top, nama_bottom):
    if not MODEL_READY:
        return "⚠️ Error", "Jalankan 'latih_model.py' dulu!"

    # Convert ke input Model
    h1, s1, v1 = colorsys.rgb_to_hsv(top_rgb[0]/255, top_rgb[1]/255, top_rgb[2]/255)
    h2, s2, v2 = colorsys.rgb_to_hsv(bottom_rgb[0]/255, bottom_rgb[1]/255, bottom_rgb[2]/255)

    # RULE KHUSUS: Warna Netral (Hitam/Putih/Abu) SELALU COCOK
    # Ini bypass biar AI gak pusing mikirin math buat warna netral
    netral_list = ["Hitam", "Putih", "Abu"]
    is_top_netral = any(x in nama_top for x in netral_list)
    is_bot_netral = any(x in nama_bottom for x in netral_list)
    
    if is_top_netral or is_bot_netral:
        return "✅ Sangat Aman", "Salah satu outfitmu netral. Pasti masuk sama apa aja!"

    # Prediksi AI (Khusus warna-warni vs warna-warni)
    input_data = np.array([[h1, s1, v1, h2, s2, v2]])
    prediksi = ai_model.predict(input_data)[0]
    probabilitas = ai_model.predict_proba(input_data)[0][1] # Seberapa yakin?

    if prediksi == 1:
        if probabilitas > 0.8:
            return "🔥 SUPER MATCH!", "Secara teori warna, ini kombinasi harmonis banget!"
        else:
            return "✅ Cocok Aja", "Masih oke dilihat mata."
    else:
        return "❌ Kurang Pas", "Warnanya agak 'berantem'. Coba ganti tone lain."