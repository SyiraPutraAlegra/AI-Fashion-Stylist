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
    # Crop tengah 30% aja biar makin fokus ke kain
    crop = image[int(h*0.35):int(h*0.65), int(w*0.35):int(w*0.65)]
    if crop.size == 0: crop = image
    pixels = crop.reshape((-1, 3))
    clt = KMeans(n_clusters=k, n_init=10)
    clt.fit(pixels)
    return clt.cluster_centers_[0].astype(int)

# --- 2. LOGIKA WARNA (FINAL TUNING) ---
def get_human_color(R, G, B):
    h, s, v = colorsys.rgb_to_hsv(R/255.0, G/255.0, B/255.0)
    hue_deg = h * 360 

    # --- LEVEL 1: CEK NETRAL (SWEET SPOT) ---
    
    # HITAM: Gelap (V < 0.22)
    if v < 0.22: return "Hitam"
    
    # PUTIH (REVISI TENGAH): 
    # Tadi 0.80 (ketinggian), 0.60 (kerendahan).
    # Sekarang kita kunci di 0.73. 
    # Artinya: Putih agak redup diterima, tapi Abu terang ditolak.
    if v > 0.73 and s < 0.18: return "Putih"
    
    # ABU-ABU: Sisanya yang pudar
    if s < 0.18: return "Abu-abu"

    # --- LEVEL 2: TENTUKAN NAMA DASAR ---
    nama_dasar = "Warna Unik"
    
    # MERAH
    if (hue_deg >= 0 and hue_deg < 15) or (hue_deg >= 340):
        nama_dasar = "Merah"
    # ORANYE
    elif 15 <= hue_deg < 40:
        nama_dasar = "Oranye"
        
    # KUNING & HIJAU (UPDATE AGRESIF)
    # Tadi Kuning sampe 70. Sekarang kita potong jadi 60.
    # Jadi warna "Lime" atau "Stabilo" (60-70) bakal masuk HIJAU.
    elif 40 <= hue_deg < 60:
        nama_dasar = "Kuning"
        
    # HIJAU: Mulai dari 60 derajat!
    elif 60 <= hue_deg < 170:
        nama_dasar = "Hijau"
        
    # SISANYA SAMA
    elif 170 <= hue_deg < 190:
        nama_dasar = "Tosca"
    elif 190 <= hue_deg < 260:
        nama_dasar = "Biru"
    elif 260 <= hue_deg < 310:
        nama_dasar = "Ungu"
    elif 310 <= hue_deg < 340:
        nama_dasar = "Pink"

    # --- LEVEL 3: TAMBAHAN LOGIKA TUA / MUDA ---
    suffix = ""
    
    # TUA: Gelap (0.22 - 0.55)
    if 0.22 <= v < 0.55:
        suffix = "Tua"
        
    # MUDA: Terang (> 0.80) DAN Pudar dikit (s < 0.65)
    # Kita naikin syarat muda biar gak sembarang warna terang dibilang muda
    elif v > 0.80 and s < 0.65:
        suffix = "Muda"

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
    is_top_netral = any(x in nama_top for x in netral_list)
    is_bot_netral = any(x in nama_bottom for x in netral_list)
    
    if is_top_netral or is_bot_netral:
        return "✅ Sangat Aman", f"Kombinasi {nama_top} & {nama_bottom} itu 'cheat code' fashion. Pasti masuk!"

    input_data = np.array([[h1, s1, v1, h2, s2, v2]])
    prediksi = ai_model.predict(input_data)[0]

    if prediksi == 1:
        return "🔥 SUPER MATCH!", f"Kombinasi {nama_top} + {nama_bottom} approved by AI!"
    else:
        return "⚠️ Kurang Masuk", f"Hmm, {nama_top} sama {nama_bottom} agak 'berantem' warnanya."
