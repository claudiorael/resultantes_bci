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
    h1 { color: #003366; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    h3 { color: #555555; }
    .stProgress > div > div > div > div { background-color: #003366; }
    </style>
    """, unsafe_allow_html=True)

def limpiar_rut(rut):
    if pd.isna(rut) or rut == '': return ""
    return re.sub(r'[^0-9kK]', '', str(rut)).upper()

@st.cache_data
def load_masters():
    tips, camps = None, None
    
    # Intentar cargar Tipificaciones con múltiples codificaciones para evitar errores silenciosos
    try: tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding='utf-8')
    except:
        try: tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding='latin1')
        except:
            try: tips = pd.read_excel('tipificaciones.xlsx')
            except: pass

    # Intentar cargar Campañas
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

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown('<div class="recaall-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Configuración")
    st.write("Verificando archivos maestros:")
    if df_tips is not None and not df_tips.empty: st.success("✅ Tipificaciones OK")
    else: st.error("❌ Tipificaciones no detectadas")
    
    if df_camps is not None and not df_camps.empty: st.success("✅ Campañas OK")
    else: st.error("❌ Campañas no detectadas")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    file = st.file_uploader("📥 Subir reporte Vicidial para procesamiento", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python', encoding='latin1')
        df_input.columns = df_input.columns.str.strip()
        
        st.info(f"📋 Se han cargado {len(df_input)} registros correctamente.")
        
        if st.button("🚀 PROCESAR"):
            bar = st.progress(0)
            status = st.empty()
            
            res = pd.DataFrame()
            
            # --- PASO 1: Identificadores y Fecha ---
            status.text("Estructurando datos base...")
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
            status.text("Calculando tiempos y nombres...")
            res['GES_nombre_cliente'] = (df_input.get('first_name', pd.Series(dtype=str)).astype(str).replace('nan', '') + " " + df_input.get('last_name', pd.Series(dtype=str)).astype(str).replace('nan', '')).str.strip()
            res['GES_estado_cliente'] = "T"
            res['FDL_identificador_documento'] = df_input.get('lead_id', '')
            res['FDL_referencia_documento'] = df_input.get('length_in_sec', pd.Series(dtype=float)).apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")
            res['FDL_username_originador'] = df_input.get('full_name', '')
            
            bar.progress(40)
            time.sleep(0.2)

            # --- PASO 3: Cruces Nativos Eficientes (Merge) ---
            status.text("Realizando cruces de datos maestros...")
            
            # Tipificaciones
            res['GES_descripcion_1'], res['GES_descripcion_2'], res['GES_descripcion_3'] = "", "", ""
            if df_tips is not None and not df_tips.empty and 'COD_VICIDIAL' in df_tips.columns and 'status' in df_input.columns:
                df_input['status_clean'] = df_input['status'].fillna('').astype(str).str.strip().str.upper()
                df_tips['COD_clean'] = df_tips['COD_VICIDIAL'].fillna('').astype(str).str.strip().str.upper()
                
                df_tips_unique = df_tips.drop_duplicates(subset=['COD_clean'])
                m_tips = pd.merge(df_input[['status_clean']], df_tips_unique, left_on='status_clean', right_on='COD_clean', how='left')
                
                res['GES_descripcion_1'] = m_tips.get('Calif_1', pd.Series(dtype=str)).fillna('').values
                res['GES_descripcion_2'] = m_tips.get('Calif_2', pd.Series(dtype=str)).fillna('').values
                res['GES_descripcion_3'] = m_tips.get('Calif_3', pd.Series(dtype=str)).fillna('').values

            bar.progress(65)
            time.sleep(0.2)

            # Campañas
            res['GES_nombre_campana_gestion'] = ""
            if df_camps is not None and not df_camps.empty and 'ORIGINAL' in df_camps.columns and 'campaign_id' in df_input.columns:
                df_input['camp_clean'] = df_input['campaign_id'].fillna('').astype(str).str.strip().str.upper()
                df_camps['ORIGINAL_clean'] = df_camps['ORIGINAL'].fillna('').astype(str).str.strip().str.upper()
                
                df_camps_unique = df_camps.drop_duplicates(subset=['ORIGINAL_clean'])
                m_camps = pd.merge(df_input[['camp_clean']], df_camps_unique, left_on='camp_clean', right_on='ORIGINAL_clean', how='left')
                
                res['GES_nombre_campana_gestion'] = m_camps.get('FINAL', pd.Series(dtype=str)).fillna('').values

            bar.progress(80)
            time.sleep(0.2)

            # --- PASO 4: Lógica Final y Orden ---
            status.text("Asignando variables finales y formato...")
            res['GES_dato_variable_27'] = call_dt.dt.strftime('%m%Y')

            es_venta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            if 'BI' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']
            res['GES_dato_variable_19'] = ""

            # Reordenamiento estricto
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
            # Aplicar MAYÚSCULAS a toda la tabla
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace(['NAN', 'NONE', '<NA>'], '')

            bar.progress(100)
            status.success("🚀 ¡Proceso completado con éxito!")
            time.sleep(0.5)
            
            st.dataframe(res.head(10))

            # --- PASO 5: Generación del Excel (Calibri 9) ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False, sheet_name='Resultante BCI')
                
                worksheet = writer.sheets['Resultante BCI']
                fuente_calibri = Font(name='Calibri', size=9)
                
                for row in worksheet.iter_rows():
                    for cell in row:
                        cell.font = fuente_calibri
            
            st.download_button(
                label="📥 DESCARGAR REPORTE RECAALL",
                data=output.getvalue(),
                file_name="RECAALL_BCI_FINAL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico durante el proceso: {e}")
