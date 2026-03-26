import streamlit as st
import pandas as pd
import re
import time
import altair as alt
from io import BytesIO
from datetime import timedelta
from openpyxl.styles import Font

# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO RECAALL
st.set_page_config(page_title="Recaall | Gestión BCI", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #003366;
        color: white;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #004080;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        color: white;
    }
    
    .recaall-card {
        padding: 25px;
        border-radius: 12px;
        background-color: white;
        border-left: 5px solid #003366;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    h1 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; margin-bottom: 0; }
    h3 { color: #555555; margin-top: 0; }
    
    .stProgress > div > div > div > div { background-color: #FF7F00 !important; }
    
    [data-testid="stFileUploadDropzone"] { min-height: 80px !important; padding: 15px !important; }
    a.header-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN Y SEGURIDAD ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    col_espacio1, col_login, col_espacio2 = st.columns([1, 1.5, 1])
    
    with col_login:
        st.write("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div class="recaall-card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown("<h1>RECAALL</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #555;'>Acceso Restringido - Plataforma BCI</h4>", unsafe_allow_html=True)
        st.write("---")
        
        clave_ingresada = st.text_input("🔒 Ingrese la clave corporativa:", type="password")
        
        if st.button("Iniciar Sesión"):
            # AQUÍ PUEDES CAMBIAR LA CONTRASEÑA
            if clave_ingresada == "Recaall2026": 
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("❌ Clave incorrecta. Intente nuevamente.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Detenemos la ejecución del resto del código si no está logueado
    st.stop()


# =====================================================================
# --- A PARTIR DE AQUÍ COMIENZA LA APLICACIÓN (SOLO SI ESTÁ LOGUEADO) ---
# =====================================================================

def limpiar_rut(rut):
    if pd.isna(rut) or rut == '': return ""
    return re.sub(r'[^0-9kK]', '', str(rut)).upper()

@st.cache_data
def load_masters():
    tips, camps = None, None
    try: tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding='utf-8')
    except:
        try: tips = pd.read_csv('tipificaciones.csv
