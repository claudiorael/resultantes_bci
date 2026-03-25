import streamlit as st
import pandas as pd
import re
import time
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
    
    /* Barra de Progreso Naranja */
    .stProgress > div > div > div > div { 
        background-color: #FF7F00 !important; 
    }
    
    /* Acortar la zona del Drag and Drop */
    [data-testid="stFileUploadDropzone"] {
        min-height: 80px !important;
        padding: 15px !important;
    }
    
    /* Ocultar iconos de anclaje de Streamlit para una vista más limpia */
    a.header-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_rut(rut):
    if pd.isna(rut) or rut == '': return ""
    return re.sub(r'[^0-9kK]', '', str(rut)).upper()

@st.cache_data
def load_masters():
    tips, camps = None, None
    
    try: tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding='utf-8')
    except:
        try: tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding='latin1')
        except:
            try: tips = pd.read_excel('tipificaciones.xlsx')
            except: pass

    try: camps = pd.read_csv('campanas.csv', sep=None, engine='python', encoding='utf-8')
    except:
        try: camps = pd.read_csv('campanas.csv', sep=None, engine='python', encoding='latin1')
        except:
            try: camps = pd.read_excel('campanas.xlsx')
            except: pass
    
    if tips is not None: tips.columns = tips.columns.str.strip()
    if camps is not None: camps.columns = camps.columns.str.strip()
    return tips, camps

df_tips, df_camps = load_masters()

# 2. INTERFAZ RECAALL
st.markdown("<h1>RECAALL CONTACT CENTER</h1>", unsafe_allow_html=True)
st.markdown("### Generador de Resultantes BCI")
st.write("---")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("#### ⚙️ Configuración")
    st.write("Verificando archivos maestros:")
    if df_tips is not None and not df_tips.empty: st.success("✅ Tipificaciones OK")
    else: st.error("❌ Tipificaciones no detectadas")
    
    if df_camps is not None and not df_camps.empty: st.success("✅ Campañas OK")
    else: st.error("❌ Campañas no detectadas")

with col2:
    file = st.file_uploader("📥 Subir reporte Vicidial (Excel o CSV)", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python', encoding='latin1')
        df_input.columns = df_input.columns.str.strip()
        
        st.info(f"📋 Se han cargado {len(df_input)} registros correctamente.")
        
        if st.button("🚀 PROCESAR"):
            bar = st.progress(0)
            status = st.empty()
            
            res = pd.DataFrame()
            
            # --- INICIO ---
            status.markdown("**0%** - Iniciando proceso...")
            time.sleep(0.2)
            
            # --- PASO 1: Identificadores y Fecha ---
            status.markdown("**20%** - Estructurando datos base e identificadores...")
            res['GES_nro_contacto'] = df_input.get('lead_id', '')
            call_dt = pd.to_datetime(df_input.get('call_date', pd.Series(dtype='datetime64[ns]')))
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')
            res['GES_username_recurso'] = df_input.get('full_name', '')
            res['GES_ani'] = df_input.get('phone_number_dialed', '')
            res['GES_id_cliente'] = df_input.get('vendor_lead_code', pd.Series(dtype=str)).apply(limpiar_rut)
            
            bar.progress(20)
            time.sleep(0.2)

            # --- PASO 2: Datos de Gestión ---
            status.markdown("**40%** - Calculando tiempos de gestión y formateando nombres...")
            res['GES_nombre_cliente'] = (df_input.get('first_name', pd.Series(dtype=str)).astype(
