import cv2
import numpy as np
import colorsys
import joblib
import os
from sklearn.cluster import KMeans

# --- LOAD MODEL ---
if os.path.exists('model_fashion_hsv.pkl'):
    ai_model = joblib.load('model_fashion_hsv.pkl')
    MODEL_READY = True
else:
    MODEL_READY = False

# --- 1. MATA (DETEKSI) ---
def get_dominant_color(image, k=1):
    image = cv2.resize(image, (64, 64))
    h, w, _ = image.shape
    # Crop tengah 40%
    crop = image[int(h*0.3):int(h*0.7), int(w*0.3):int(w*0.7)]
    if crop.size == 0: crop = image
    pixels = crop.reshape((-1, 3))
    clt = KMeans(n_clusters=k, n_init=10)
    clt.fit(pixels)
    return clt.cluster_centers_[0].astype(int)

# --- 2. LOGIKA WARNA + TUA/MUDA ---
def get_human_color(R, G, B):
    h, s, v = colorsys.rgb_to_hsv(R/255.0, G/255.0, B/255.0)
    hue_deg = h * 360 

    # --- LEVEL 1: CEK NETRAL (JANGAN KASIH EMBEL-EMBEL TUA/MUDA) ---
    if v < 0.20: return "Hitam"
    if v > 0.60 and s < 0.15: return "Putih"
    if s < 0.15: return "Abu-abu"

    # --- LEVEL 2: TENTUKAN NAMA DASAR ---
    nama_dasar = "Warna Unik"
    
    if (hue_deg >= 0 and hue_deg < 15) or (hue_deg >= 340):
        nama_dasar = "Merah"
    elif 15 <= hue_deg < 40:
        nama_dasar = "Oranye"
    elif 40 <= hue_deg < 65:
        nama_dasar = "Kuning"
    elif 65 <= hue_deg < 170:
        nama_dasar = "Hijau"
    elif 170 <= hue_deg < 190:
        nama_dasar = "Tosca"
    elif 190 <= hue_deg < 260:
        nama_dasar = "Biru"
    elif 260 <= hue_deg < 310:
        nama_dasar = "Ungu"
    elif 310 <= hue_deg < 340:
        nama_dasar = "Pink"

    # --- LEVEL 3: TAMBAHAN LOGIKA TUA / MUDA ---
    # Kita cek Value (Kecerahan)
    suffix = ""
    
    # Kalau Value rendah (0.2 - 0.5) -> Gelap/Tua
    # (Tapi jangan terlalu gelap, nanti jadi Hitam)
    if 0.20 <= v < 0.50:
        suffix = "Tua"
        
    # Kalau Value tinggi (> 0.85) DAN Saturasi agak rendah (< 0.6) -> Terang/Muda/Pastel
    # Syarat saturasi penting biar warna "Neon" gak dibilang muda.
    elif v > 0.80 and s < 0.70:
        suffix = "Muda"

    # Gabungin namanya (Contoh: "Biru" + " " + "Tua" = "Biru Tua")
    nama_final = f"{nama_dasar} {suffix}".strip()
    
    return nama_final

# --- 3. OTAK KECOCOKAN ---
def check_compatibility(top_rgb, bottom_rgb, nama_top, nama_bottom):
    if not MODEL_READY:
        return "⚠️ Error", "Model belum siap."

    h1, s1, v1 = colorsys.rgb_to_hsv(top_rgb[0]/255, top_rgb[1]/255, top_rgb[2]/255)
    h2, s2, v2 = colorsys.rgb_to_hsv(bottom_rgb[0]/255, bottom_rgb[1]/255, bottom_rgb[2]/255)

    # BYPASS NETRAL
    netral_list = ["Hitam", "Putih", "Abu"]
    # Kita cek substring, biar "Abu-abu Tua" tetep dianggap Netral
    is_top_netral = any(x in nama_top for x in netral_list)
    is_bot_netral = any(x in nama_bottom for x in netral_list)
    
    if is_top_netral or is_bot_netral:
        return "✅ Sangat Aman", "Warna netral (Hitam/Putih/Abu) selalu cocok sama apa aja!"

    input_data = np.array([[h1, s1, v1, h2, s2, v2]])
    prediksi = ai_model.predict(input_data)[0]

    if prediksi == 1:
        return "🔥 SUPER MATCH!", f"Kombinasi {nama_top} dan {nama_bottom} harmonis banget!"
    else:
        return "❌ Kurang Pas", f"Waduh, {nama_top} ketemu {nama_bottom} agak nabrak nih."

