import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import timedelta

st.set_page_config(page_title="Procesador BCI - Recaall", layout="wide")

# Función para cargar maestros desde el repositorio de GitHub
@st.cache_data
def load_masters():
    try:
        # Cargamos los archivos que subiste a GitHub
        tips = pd.read_csv('tipificaciones.csv')
        camps = pd.read_csv('campanas.csv')
        return tips, camps
    except Exception as e:
        return None, None

df_tips, df_camps = load_masters()

st.title("🏦 Sistema de Resultantes BCI")
st.markdown("Carga el reporte de Vicidial para generar la resultante con las reglas del cliente.")

if df_tips is None or df_camps is None:
    st.warning("⚠️ No se encontraron 'tipificaciones.csv' o 'campanas.csv' en GitHub. Súbelos para habilitar los cruces automáticos.")

file = st.file_uploader("Subir Reporte Vicidial (Excel o CSV)", type=["xlsx", "csv"])

if file:
    # Leer el archivo de entrada
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        st.write("### Datos Originales detectados")
        st.dataframe(df_input.head(3))
        
        if st.button("🚀 Generar Resultante BCI"):
            res = pd.DataFrame()

            # 1. Identificadores y Usuarios
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code']
            
            # 2. Fechas y Horas (Separación desde call_date)
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')

            # 3. Nombre Cliente y Estado Fijo
            res['GES_nombre_cliente'] = (df_input['first_name'].fillna('') + " " + 
                                        df_input['middle_initial'].fillna('') + " " + 
                                        df_input['last_name'].fillna('')).str.strip()
            res['GES_estado_cliente'] = "T"

            # 4. Duración (Segundos a HH:MM:SS) - CORREGIDO
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")

            # 5. Cruce con Tipificaciones (Descripciones 1, 2 y 3)
            if df_tips is not None:
                df_merged_tips = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                res['GES_descripcion_1'] = df_merged_tips['Calif_1']
                res['GES_descripcion_2'] = df_merged_tips['Calif_2']
                res['GES_descripcion_3'] = df_merged_tips['Calif_3']

            # 6.
