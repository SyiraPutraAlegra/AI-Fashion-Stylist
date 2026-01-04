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
    # Crop tengah 35%
    crop = image[int(h*0.35):int(h*0.65), int(w*0.35):int(w*0.65)]
    if crop.size == 0: crop = image
    pixels = crop.reshape((-1, 3))
    clt = KMeans(n_clusters=k, n_init=10)
    clt.fit(pixels)
    return clt.cluster_centers_[0].astype(int)

# --- 2. LOGIKA WARNA PREMIUM (KAMUS 50 WARNA) ---
def get_human_color(R, G, B):
    h, s, v = colorsys.rgb_to_hsv(R/255.0, G/255.0, B/255.0)
    hue_deg = h * 360 

    # === TIER 1: ACHROMATIC (Gak ada warna) ===
    if v < 0.18: return "Hitam" # Gelap banget
    if v < 0.30 and s < 0.15: return "Charcoal / Abu Tua" # Abu gelap keren
    if v > 0.78 and s < 0.10: return "Putih" # Putih bersih
    if s < 0.15: return "Abu-abu" # Abu standar

    # === TIER 2: WARNA SPESIFIK (Detektif Mode On) ===
    
    # --- KELOMPOK MERAH / PINK (340 - 15) ---
    if (hue_deg >= 340 or hue_deg < 15):
        if v < 0.50: return "Maroon / Burgundy"
        if s < 0.50 and v > 0.80: return "Peach / Salmon"
        if s > 0.70 and v > 0.80: return "Fuschia / Hot Pink"
        return "Merah"

    # --- KELOMPOK ORANYE / COKLAT (15 - 45) ---
    elif (15 <= hue_deg < 45):
        if v < 0.50: return "Coklat Tua"
        if v < 0.70 and s > 0.60: return "Terracotta / Bata"
        if v > 0.80 and s < 0.35: return "Cream / Nude"
        if 0.40 < s < 0.60 and 0.50 < v < 0.80: return "Camel / Khaki" # Warna celana chino
        return "Oranye"

    # --- KELOMPOK KUNING (45 - 65) ---
    elif (45 <= hue_deg < 65):
        if s > 0.60 and v < 0.75: return "Mustard"
        if v > 0.90 and s < 0.50: return "Broken White / Ivory"
        return "Kuning"

    # --- KELOMPOK HIJAU (65 - 165) ---
    elif (65 <= hue_deg < 165):
        if v < 0.40: return "Emerald / Hijau Botol"
        if v < 0.60 and s < 0.50: return "Army / Olive"
        if v > 0.80 and s < 0.40: return "Sage / Mint"
        if s > 0.80 and v > 0.80: return "Lime / Stabilo"
        return "Hijau"

    # --- KELOMPOK CYAN / BIRU (165 - 260) ---
    elif (165 <= hue_deg < 260):
        if 165 <= hue_deg < 200: # Area Tosca
            if v < 0.50: return "Teal / Tosca Gelap"
            return "Tosca / Cyan"
        else: # Area Biru
            if v < 0.35: return "Navy"
            if s < 0.30 and 0.40 < v < 0.70: return "Denim / Steel Blue"
            if v > 0.85 and s < 0.40: return "Sky Blue / Baby Blue"
            if s > 0.80 and v > 0.80: return "Electric Blue"
            return "Biru"

    # --- KELOMPOK UNGU (260 - 340) ---
    elif (260 <= hue_deg < 340):
        if v > 0.80 and s < 0.40: return "Lilac / Lavender"
        if v < 0.45: return "Plum / Ungu Tua"
        return "Ungu"

    return "Warna Unik"

# --- 3. OTAK KECOCOKAN (UPDATE DAFTAR NETRAL) ---
def check_compatibility(top_rgb, bottom_rgb, nama_top, nama_bottom):
    if not MODEL_READY:
        return "⚠️ Error", "Model belum siap."

    h1, s1, v1 = colorsys.rgb_to_hsv(top_rgb[0]/255, top_rgb[1]/255, top_rgb[2]/255)
    h2, s2, v2 = colorsys.rgb_to_hsv(bottom_rgb[0]/255, bottom_rgb[1]/255, bottom_rgb[2]/255)

    # 1. BYPASS NETRAL (Daftar ini makin panjang karena warna bumi itu gampang dimatch)
    # Warna-warna ini dianggap "Aman" ketemu apa aja.
    safe_words = [
        "Hitam", "Putih", "Abu", "Charcoal", 
        "Cream", "Nude", "Navy", "Denim", 
        "Khaki", "Camel", "Broken White"
    ]
    
    is_top_safe = any(word in nama_top for word in safe_words)
    is_bot_safe = any(word in nama_bottom for word in safe_words)
    
    if is_top_safe or is_bot_safe:
        return "✅ Sangat Aman", f"Salah satu outfitmu ({nama_top} / {nama_bottom}) adalah warna Netral/Versatile. Gas terus!"

    # 2. SATPAM ANTI-NORAK 🛡️
    # Mencegah kombinasi sakit mata (Saturasi tinggi ketemu Saturasi tinggi)
    if s1 > 0.70 and s2 > 0.70:
        # Cek kalau warnanya beda jauh (Contrast Clash)
        diff = abs(h1 - h2)
        if 0.25 < diff < 0.75: # Bukan tetangga, bukan komplementer pas
            return "⚠️ Hati-hati", "Ini kombinasi 'Color Block' yang berani banget. Pastikan kamu PD makenya!"

    # 3. PREDIKSI AI
    input_data = np.array([[h1, s1, v1, h2, s2, v2]])
    prediksi = ai_model.predict(input_data)[0]

    if prediksi == 1:
        return "🔥 SUPER MATCH!", f"Kombinasi {nama_top} + {nama_bottom} terlihat harmonis!"
    else:
        return "⚠️ Kurang Masuk", f"Hmm, tone warnanya agak kurang nyatu. Coba salah satu diganti netral."
