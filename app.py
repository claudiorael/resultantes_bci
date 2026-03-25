import streamlit as st
import pandas as pd
import re
import time
from io import BytesIO
from datetime import timedelta

st.set_page_config(page_title="Procesador BCI - Recaall", layout="wide")

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

st.title("🏦 Sistema de Resultantes BCI")
st.markdown("Carga tu reporte de Vicidial para transformarlo al formato final en **MAYÚSCULAS**.")

file = st.file_uploader("Subir Reporte Vicidial", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python')
        df_input.columns = df_input.columns.str.strip()
        
        st.write("### Vista previa de datos cargados")
        st.dataframe(df_input.head(3))
        
        if st.button("🚀 Generar Resultante BCI"):
            # Inicializar barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            res = pd.DataFrame()

            # Etapa 1: Datos básicos y RUT
            status_text.text("Procesando identificadores y RUT...")
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code'].apply(limpiar_rut)
            progress_bar.progress(25)
            time.sleep(0.3)

            # Etapa 2: Fechas y Tiempos
            status_text.text("Calculando fechas y duraciones...")
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(
                lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00"
            )
            progress_bar.progress(50)
            time.sleep(0.3)

            # Etapa 3: Nombres y Cruces
            status_text.text("Realizando cruces con maestros y formateando nombres...")
            res['GES_nombre_cliente'] = (
                df_input['first_name'].astype(str).replace('nan', '') + " " + 
                df_input['middle_initial'].astype(str).replace('nan', '') + " " + 
                df_input['last_name'].astype(str).replace('nan', '')
            ).str.strip()
            res['GES_estado_cliente'] = "T"

            if df_tips is not None and 'COD_VICIDIAL' in df_tips.columns:
                df_tips['COD_VICIDIAL'] = df_tips['COD_VICIDIAL'].astype(str)
                df_input['status'] = df_input['status'].astype(str)
                df_merged_t = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                res['GES_descripcion_1'] = df_merged_t['Calif_1']
                res['GES_descripcion_2'] = df_merged_t['Calif_2']
                res['GES_descripcion_3'] = df_merged_t['Calif_3']

            if df_camps is not None and 'ORIGINAL' in df_camps.columns:
                df_camps['ORIGINAL'] = df_camps['ORIGINAL'].astype(str)
                df_input['campaign_id'] = df_input['campaign_id'].astype(str)
                df_merged_c = pd.merge(df_input[['campaign_id']], df_camps, left_on='campaign_id', right_on='ORIGINAL', how='left')
                res['GES_nombre_campana_gestion'] = df_merged_c['FINAL']
                res['GES_dato_variable_27'] = df_merged_c['GES_dato_variable_27']
            
            progress_bar.progress(75)
            time.sleep(0.3)

            # Etapa 4: Lógica de Venta y Mayúsculas
            status_text.text("Finalizando formato en MAYÚSCULAS...")
            es_venta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            if 'BI' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']

            # Transformación final
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace(['NAN', 'NONE', '<NA>'], '')
            
            progress_bar.progress(100)
            status_text.text("¡Proceso completado!")
            time.sleep(0.5)
            status_text.empty() # Limpiar texto de estado

            st.success("¡Resultante generada con éxito!")
            st.dataframe(res.head())

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Reporte en MAYÚSCULAS", 
                data=output.getvalue(), 
                file_name="Resultante_BCI.xlsx"
            )

    except Exception as e:
        st.error(f"Error técnico: {e}")
