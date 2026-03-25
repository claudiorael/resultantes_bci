import streamlit as st
import pandas as pd
import re
import time
from io import BytesIO
from datetime import timedelta

# 1. CONFIGURACIÓN Y ESTILO (Poner la página "bonita")
st.set_page_config(page_title="Resultantes BCI | Recaall", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #002e5d;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
    .stProgress > div > div > div > div {
        background-color: #002e5d;
    }
    h1 {
        color: #002e5d;
        font-family: 'Helvetica Neue', sans-serif;
    }
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

# 2. INTERFAZ DE USUARIO
st.title("🏦 Sistema de Resultantes BCI")
st.subheader("Transformación automatizada de reportes Vicidial")

with st.sidebar:
    st.image("https://www.bci.cl/assets/img/bci-logo.png", width=100) # Opcional: Logo cliente
    st.markdown("### Estado de Maestros")
    if df_tips is not None: st.success("✅ Tipificaciones cargadas")
    else: st.error("❌ Falta tipificaciones.csv")
    
    if df_camps is not None: st.success("✅ Campañas cargadas")
    else: st.error("❌ Falta campanas.csv")

file = st.file_uploader("📂 Selecciona el reporte Vicidial (Excel o CSV)", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python')
        df_input.columns = df_input.columns.str.strip()
        
        st.info(f"Registros detectados: {len(df_input)}")
        
        if st.button("🚀 INICIAR PROCESAMIENTO"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            res = pd.DataFrame()

            # --- PASO 1: IDENTIFICADORES ---
            status_text.text("Estructurando identificadores...")
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code'].apply(limpiar_rut)
            progress_bar.progress(20)

            # --- PASO 2: TIEMPOS ---
            status_text.text("Calculando tiempos de gestión...")
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(
                lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) and str(x).isdigit() else "00:00:00"
            )
            progress_bar.progress(40)

            # --- PASO 3: CRUCE TIPIFICACIONES (CALIF_3) ---
            status_text.text("Cruzando tipificaciones (Calif_1, 2, 3)...")
            res['GES_descripcion_1'] = ""
            res['GES_descripcion_2'] = ""
            res['GES_descripcion_3'] = ""

            if df_tips is not None and 'COD_VICIDIAL' in df_tips.columns:
                df_tips['COD_VICIDIAL'] = df_tips['COD_VICIDIAL'].astype(str)
                df_input['status'] = df_input['status'].astype(str)
                df_merged_t = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                
                # Asignación de Calif_3 a GES_descripcion_3
                if 'Calif_1' in df_merged_t.columns: res['GES_descripcion_1'] = df_merged_t['Calif_1']
                if 'Calif_2' in df_merged_t.columns: res['GES_descripcion_2'] = df_merged_t['Calif_2']
                if 'Calif_3' in df_merged_t.columns: res['GES_descripcion_3'] = df_merged_t['Calif_3']
            progress_bar.progress(60)

            # --- PASO 4: CRUCE CAMPAÑAS ---
            status_text.text("Cruzando campañas y variables...")
            res['GES_nombre_campana_gestion'] = ""
            res['GES_dato_variable_27'] = ""

            if df_camps is not None and 'ORIGINAL' in df_camps.columns:
                df_camps['ORIGINAL'] = df_camps['ORIGINAL'].astype(str)
                df_input['campaign_id'] = df_input['campaign_id'].astype(str)
                df_merged_c = pd.merge(df_input[['campaign_id']], df_camps, left_on='campaign_id', right_on='ORIGINAL', how='left')
                
                if 'FINAL' in df_merged_c.columns: res['GES_nombre_campana_gestion'] = df_merged_c['FINAL']
                if 'GES_dato_variable_27' in df_merged_c.columns: res['GES_dato_variable_27'] = df_merged_c['GES_dato_variable_27']
            progress_bar.progress(80)

            # --- PASO 5: LÓGICA DE VENTAS Y FORMATO ---
            status_text.text("Aplicando formato final MAYÚSCULAS...")
            res['GES_nombre_cliente'] = (df_input['first_name'].astype(str).replace('nan', '') + " " + df_input['last_name'].astype(str).replace('nan', '')).str.strip()
            res['GES_estado_cliente'] = "T"
            
            # Lógica Venta
            es_venta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            if 'BI' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']

            # TODO A MAYÚSCULAS
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace(['NAN', 'NONE', '<NA>'], '')
            
            progress_bar.progress(100)
            status_text.success("✅ ¡Procesamiento finalizado!")

            st.dataframe(res.head(10))

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 DESCARGAR EXCEL RESULTANTE",
                data=output.getvalue(),
                file_name="Resultante_BCI_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Hubo un problema: {e}")
