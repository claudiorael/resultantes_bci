import streamlit as st
import pandas as pd
import re
import time
from io import BytesIO
from datetime import timedelta

# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO RECAALL
st.set_page_config(page_title="Recaall | Gestión BCI", layout="wide", page_icon="📈")

# Colores Recaall: Azul profundo (#003366), Gris/Fondo (#F4F7F9), Texto (#333333)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    /* Botón Principal */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #003366; /* Azul Recaall */
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
    
    /* Tarjetas de información */
    .recaall-card {
        padding: 25px;
        border-radius: 12px;
        background-color: white;
        border-left: 5px solid #003366;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Títulos */
    h1 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    h3 { color: #555555; }
    
    /* Barra de Progreso */
    .stProgress > div > div > div > div { background-color: #003366; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_rut(rut):
    if pd.isna(rut) or rut == '': return ""
    return re.sub(r'[^0-9kK]', '', str(rut)).upper()

@st.cache_data
def load_masters():
    tips, camps = None, None
    try:
        tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python')
    except:
        try: tips = pd.read_excel('tipificaciones.xlsx')
        except: pass
    try:
        camps = pd.read_csv('campanas.csv', sep=None, engine='python')
    except:
        try: camps = pd.read_excel('campanas.xlsx')
        except: pass
    
    if tips is not None: tips.columns = tips.columns.str.strip()
    if camps is not None: camps.columns = camps.columns.str.strip()
    return tips, camps

df_tips, df_camps = load_masters()

# 2. INTERFAZ RECAALL
st.markdown("<h1>RECAALL <span style='font-weight:100; color:#888;'>| Servicios Financieros</span></h1>", unsafe_allow_html=True)
st.markdown("### Generador de Resultantes BCI")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown('<div class="recaall-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Configuración")
    st.write("Verificando archivos maestros en el servidor:")
    if df_tips is not None: st.success("✅ Tipificaciones OK")
    else: st.error("❌ Tipificaciones no detectadas")
    
    if df_camps is not None: st.success("✅ Campañas OK")
    else: st.error("❌ Campañas no detectadas")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    file = st.file_uploader("📥 Subir reporte Vicidial para procesamiento", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python')
        df_input.columns = df_input.columns.str.strip()
        
        st.info(f"📋 Se han cargado {len(df_input)} registros correctamente.")
        
        if st.button("🚀 PROCESAR Y CONVERTIR A MAYÚSCULAS"):
            bar = st.progress(0)
            status = st.empty()
            
            # --- PROCESAMIENTO ---
            res = pd.DataFrame()
            
            # Paso 1: Identificadores
            status.text("Estructurando datos base...")
            res['GES_nro_contacto'] = df_input['lead_id']
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')
            res['GES_username_recurso'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code'].apply(limpiar_rut)
            bar.progress(20)

            # Paso 2: Datos de Gestión
            status.text("Calculando tiempos y nombres...")
            res['GES_nombre_cliente'] = (df_input['first_name'].astype(str).replace('nan', '') + " " + df_input['last_name'].astype(str).replace('nan', '')).str.strip()
            res['GES_estado_cliente'] = "T"
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")
            res['FDL_username_originador'] = df_input['full_name']
            bar.progress(45)

            # Paso 3: Cruces (Tipificaciones)
            status.text("Realizando cruce de tipificaciones (Calif_3)...")
            res['GES_descripcion_1'], res['GES_descripcion_2'], res['GES_descripcion_3'] = "", "", ""
            if df_tips is not None and 'COD_VICIDIAL' in df_tips.columns:
                df_input['status'] = df_input['status'].astype(str)
                df_tips['COD_VICIDIAL'] = df_tips['COD_VICIDIAL'].astype(str)
                m_tips = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                res['GES_descripcion_1'] = m_tips.get('Calif_1', "")
                res['GES_descripcion_2'] = m_tips.get('Calif_2', "")
                res['GES_descripcion_3'] = m_tips.get('Calif_3', "")
            bar.progress(70)

            # Paso 4: Cruces (Campañas)
            status.text("Realizando cruce de campañas...")
            res['GES_nombre_campana_gestion'], res['GES_dato_variable_27'] = "", ""
            if df_camps is not None and 'ORIGINAL' in df_camps.columns:
                df_input['campaign_id'] = df_input['campaign_id'].astype(str)
                df_camps['ORIGINAL'] = df_camps['ORIGINAL'].astype(str)
                m_camps = pd.merge(df_input[['campaign_id']], df_camps, left_on='campaign_id', right_on='ORIGINAL', how='left')
                res['GES_nombre_campana_gestion'] = m_camps.get('FINAL', "")
                res['GES_dato_variable_27'] = m_camps.get('GES_dato_variable_27', "")
            bar.progress(85)

            # Paso 5: Lógica Final y Reordenamiento
            status.text("Finalizando validaciones...")
            es_venta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            if 'BI' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']
            res['GES_dato_variable_19'] = ""

            # Orden estricto solicitado
            orden_columnas = [
                'GES_nro_contacto', 'GES_fecha_creacion', 'GES_hora_min_creacion', 
                'GES_username_recurso', 'GES_ani', 'GES_id_cliente', 
                'GES_nombre_cliente', 'GES_estado_cliente', 'FDL_identificador_documento', 
                'FDL_referencia_documento', 'FDL_username_originador', 'GES_descripcion_1', 
                'GES_descripcion_2', 'GES_descripcion_3', 'GES_nombre_campana_gestion', 
                'GES_dato_variable_05', 'GES_dato_variable_26', 'GES_dato_variable_27', 
                'GES_dato_variable_19'
            ]
            
            res = res.reindex(columns=orden_columnas)
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace(['NAN', 'NONE', '<NA>'], '')

            bar.progress(100)
            status.success("🚀 ¡Resultante lista para descarga!")
            st.dataframe(res.head(10))

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 DESCARGAR REPORTE RECAALL (MAYÚSCULAS)",
                data=output.getvalue(),
                file_name="RECAALL_BCI_FINAL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico durante el proceso: {e}")
