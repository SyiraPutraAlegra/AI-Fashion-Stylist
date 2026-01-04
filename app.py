import streamlit as st
import cv2
import numpy as np
from gtts import gTTS
from io import BytesIO
from brain import get_dominant_color, get_human_color, check_compatibility

# --- CONFIG ---
st.set_page_config(page_title="AI Fashion Stylist", page_icon="✨")

# --- CSS SIMPEL BIAR RAPI ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI AUDIO ---
def play_audio(text):
    try:
        tts = gTTS(text=text, lang='id')
        sound = BytesIO()
        tts.write_to_fp(sound)
        st.audio(sound, format='audio/mp3')
    except:
        pass

# --- SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'data_baju' not in st.session_state: st.session_state.data_baju = None
if 'data_celana' not in st.session_state: st.session_state.data_celana = None

def reset():
    st.session_state.step = 1
    st.session_state.data_baju = None
    st.session_state.data_celana = None

# HEADER
st.title("✨ AI Fashion Stylist")
st.write("Cek kecocokan outfit kamu dengan kecerdasan buatan.")

# ==========================================
# LANGKAH 1: FOTO BAJU
# ==========================================
if st.session_state.step == 1:
    st.info("📸 Foto bagian **BAJU (Atasan)** kamu")
    img = st.camera_input("Kamera Baju", key="cam1")
    
    if img:
        bytes_data = img.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        
        dom_rgb = get_dominant_color(rgb_img)
        nama_warna = get_human_color(dom_rgb[0], dom_rgb[1], dom_rgb[2])
        
        st.session_state.data_baju = {'rgb': dom_rgb, 'img': rgb_img, 'warna': nama_warna}
        st.success(f"Terdeteksi: {nama_warna}")
        
        if st.button("Lanjut ke Celana ➡️"):
            st.session_state.step = 2
            st.rerun()

# ==========================================
# LANGKAH 2: FOTO CELANA
# ==========================================
elif st.session_state.step == 2:
    st.image(st.session_state.data_baju['img'], width=100, caption="Baju")
    
    st.info("📸 Sekarang foto **CELANA (Bawahan)**")
    img = st.camera_input("Kamera Celana", key="cam2")
    
    if img:
        bytes_data = img.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        
        dom_rgb = get_dominant_color(rgb_img)
        nama_warna = get_human_color(dom_rgb[0], dom_rgb[1], dom_rgb[2])
        
        st.session_state.data_celana = {'rgb': dom_rgb, 'img': rgb_img, 'warna': nama_warna}
        st.success(f"Terdeteksi: {nama_warna}")
        
        if st.button("✨ ANALISIS KECOCOKAN ✨"):
            st.session_state.step = 3
            st.rerun()
            
    if st.button("⬅️ Ulang"):
        reset()
        st.rerun()

# ==========================================
# LANGKAH 3: HASIL
# ==========================================
elif st.session_state.step == 3:
    baju = st.session_state.data_baju
    celana = st.session_state.data_celana
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.image(baju['img'], caption=f"Atasan: {baju['warna']}")
    c2.image(celana['img'], caption=f"Bawahan: {celana['warna']}")
    
    # AI MIKIR DISINI
    judul, pesan = check_compatibility(baju['rgb'], celana['rgb'], baju['warna'], celana['warna'])
    
    st.header(judul)
    st.write(pesan)
    
    # Efek Visual & Audio
    if "MATCHING" in judul or "Oke" in judul or "Aesthetic" in judul:
        st.balloons()
    
    play_audio(f"{judul}. {pesan}")
    
    st.markdown("---")
    if st.button("🔄 Cek Outfit Lain"):
        reset()
        st.rerun()