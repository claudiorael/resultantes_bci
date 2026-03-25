import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import timedelta

# Configuración de la página
st.set_page_config(page_title="Procesador BCI - Recaall", layout="wide")

# Función para cargar los archivos maestros desde GitHub de forma interna
@st.cache_data
def load_masters():
    try:
        # Intentamos cargar los archivos desde el repositorio
        tips = pd.read_csv('tipificaciones.csv')
        camps = pd.read_csv('campanas.csv')
        return tips, camps
    except Exception as e:
        return None, None

# Carga inicial de datos maestros
df_tips, df_camps = load_masters()

st.title("🏦 Sistema de Resultantes BCI")
st.markdown("Carga el reporte de Vicidial para generar la resultante con las reglas del cliente.")

# Verificación de maestros
if df_tips is None or df_camps is None:
    st.error("⚠️ Error: No se encuentran los archivos 'tipificaciones.csv' o 'campanas.csv' en GitHub.")
    st.info("Asegúrate de haber subido los archivos con esos nombres exactos a tu repositorio.")

# Cargador del reporte de Vicidial
file = st.file_uploader("Subir Reporte Vicidial (Excel o CSV)", type=["xlsx", "csv"])

if file and df_tips is not None and df_camps is not None:
    # Leer el archivo de entrada
    if file.name.endswith('xlsx'):
        df_input = pd.read_excel(file)
    else:
        df_input = pd.read_csv(file)
    
    st.write("### Vista previa de datos originales", df_input.head(3))

    if st.button("🚀 Generar Resultante BCI"):
        try:
            res = pd.DataFrame()

            # 1. Identificadores básicos
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code']
            
            # 2. Fechas y Horas (Procesamiento de call_date)
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')

            # 3. Identidad del Cliente
            res['GES_nombre_cliente'] = (df_input['first_name'].fillna('') + " " + 
                                        df_input['middle_initial'].fillna('') + " " + 
                                        df_input['last_name'].fillna('')).str.strip()
            res['GES_estado_cliente'] = "T"

            # 4. Duración de llamada (Segundos a HH:MM:SS)
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(
