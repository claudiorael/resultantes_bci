import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import timedelta

# Configuración de la página
st.set_page_config(page_title="Procesador BCI - Recaall", layout="wide")

# Función para validar y limpiar RUT
def limpiar_rut(rut):
    if pd.isna(rut) or rut == '':
        return ""
    # Dejar solo números y la letra K
    rut_limpio = re.sub(r'[^0-9kK]', '', str(rut))
    return rut_limpio.upper()

# Función para cargar maestros desde GitHub
@st.cache_data
def load_masters():
    tips, camps = None, None
    try:
        tips = pd.read_csv('tipificaciones.csv')
    except:
        try:
            tips = pd.read_excel('tipificaciones.xlsx')
        except:
            pass
    try:
        camps = pd.read_csv('campanas.csv')
    except:
        try:
            camps = pd.read_excel('campanas.xlsx')
        except:
            pass
    return tips, camps

df_tips, df_camps = load_masters()

st.title("🏦 Sistema de Resultantes BCI")
st.markdown("Procesador de reportes con validador de RUT y salida en **MAYÚSCULAS**.")

file = st.file_uploader("Subir Reporte Vicidial (Excel o CSV)", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        
        st.write("### Vista previa de datos originales")
        st.dataframe(df_input.head(3))
        
        if st.button("🚀 Generar Resultante BCI"):
            res = pd.DataFrame()

            # 1. Identificadores y Validación de RUT
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            
            # Aplicamos la limpieza de RUT a GES_id_cliente
            res['GES_id_cliente'] = df_input['vendor_lead_code'].apply(limpiar_rut)
            
            # 2. Fechas y Horas
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')

            # 3. Nombre Cliente
            res['GES_nombre_cliente'] = (df_input['first_name'].fillna('') + " " + 
                                        df_input['middle_initial'].fillna('') + " " + 
                                        df_input['last_name'].fillna('')).str.strip()
            res['GES_estado_cliente'] = "T"

            # 4. Duración
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(
                lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00"
            )

            # 5. Cruces (Tipificaciones)
            if df_tips is not None:
                df_input['status'] = df_input['status'].astype(str)
                df_tips['COD_VICIDIAL'] = df_tips['COD_VICIDIAL'].astype(str)
                df_merged_tips = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                res['GES_descripcion_1'] = df_merged_tips['Calif_1']
                res['GES_descripcion_2'] = df_merged_tips['Calif_2']
                res['GES_descripcion_3'] = df_merged_tips['Calif_3']

            # 6. Cruces (Campañas)
            if df_camps is not None:
                df_input['campaign_id'] = df_input['campaign_id'].astype(str)
                df_camps['ORIGINAL'] = df_camps['ORIGINAL'].astype(str)
                df_merged_camps = pd.merge(df_input[['campaign_id']], df_camps, left_on='campaign_id', right_on='ORIGINAL', how='left')
                res['GES_nombre_campana_gestion'] = df_merged_camps['FINAL']
                res['GES_dato_variable_27'] = df_merged_camps['GES_dato_variable_27']

            # 7. Lógica de Ventas
            es_venta = res['GES_descripcion_3'].fillna('').str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            
            if 'BI' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']

            # --- TRANSFORMACIÓN FINAL A MAYÚSCULAS ---
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace('NAN', '')

            # 8. Mostrar Resultado y Descarga
            st.success("¡Resultante procesada! RUTs validados y formato en MAYÚSCULAS.")
            st.dataframe(res.head())

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Reporte Final BCI",
                data=output.getvalue(),
                file_name="Resultante_BCI_Validador.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico: {e}")
