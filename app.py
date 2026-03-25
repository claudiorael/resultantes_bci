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
    rut_str = str(rut)
    rut_limpio = re.sub(r'[^0-9kK]', '', rut_str)
    return rut_limpio.upper()

# Función para cargar maestros (CSV o Excel)
@st.cache_data
def load_masters():
    tips, camps = None, None
    # Cargar Tipificaciones
    try:
        tips = pd.read_csv('tipificaciones.csv', sep=None, engine='python')
    except:
        try:
            tips = pd.read_excel('tipificaciones.xlsx')
        except:
            pass
            
    # Cargar Campañas
    try:
        camps = pd.read_csv('campanas.csv', sep=None, engine='python')
    except:
        try:
            camps = pd.read_excel('campanas.xlsx')
        except:
            pass
            
    return tips, camps

df_tips, df_camps = load_masters()

st.title("🏦 Sistema de Resultantes BCI")
st.markdown("Procesador de reportes con salida automática en **MAYÚSCULAS**.")

# Verificación visual para el usuario
if df_tips is not None:
    st.sidebar.success("✅ Maestro Tipificaciones cargado")
else:
    st.sidebar.error("❌ Falta 'tipificaciones.csv' o '.xlsx'")

if df_camps is not None:
    st.sidebar.success("✅ Maestro Campañas cargado")
else:
    st.sidebar.error("❌ Falta 'campanas.csv' o '.xlsx'")

file = st.file_uploader("Subir Reporte Vicidial", type=["xlsx", "csv"])

if file:
    try:
        df_input = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file, sep=None, engine='python')
        
        if st.button("🚀 Generar Resultante BCI"):
            res = pd.DataFrame()

            # 1. Identificadores
            res['GES_nro_contacto'] = df_input['lead_id']
            res['FDL_identificador_documento'] = df_input['lead_id']
            res['GES_username_recurso'] = df_input['full_name']
            res['FDL_username_originador'] = df_input['full_name']
            res['GES_ani'] = df_input['phone_number_dialed']
            res['GES_id_cliente'] = df_input['vendor_lead_code'].apply(limpiar_rut)
            
            # 2. Fechas y Horas
            call_dt = pd.to_datetime(df_input['call_date'])
            res['GES_fecha_creacion'] = call_dt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = call_dt.dt.strftime('%H:%M:%S')

            # 3. Nombre Cliente
            res['GES_nombre_cliente'] = (
                df_input['first_name'].astype(str).replace('nan', '') + " " + 
                df_input['middle_initial'].astype(str).replace('nan', '') + " " + 
                df_input['last_name'].astype(str).replace('nan', '')
            ).str.strip()
            res['GES_estado_cliente'] = "T"

            # 4. Duración
            res['FDL_referencia_documento'] = df_input['length_in_sec'].apply(
                lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) and str(x).isdigit() else "00:00:00"
            )

            # 5. Cruce Tipificaciones (Manejo de error 'COD_VICIDIAL')
            if df_tips is not None and 'COD_VICIDIAL' in df_tips.columns:
                df_input['status'] = df_input['status'].astype(str)
                df_tips['COD_VICIDIAL'] = df_tips['COD_VICIDIAL'].astype(str)
                df_merged_tips = pd.merge(df_input[['status']], df_tips, left_on='status', right_on='COD_VICIDIAL', how='left')
                res['GES_descripcion_1'] = df_merged_tips.get('Calif_1', '')
                res['GES_descripcion_2'] = df_merged_tips.get('Calif_2', '')
                res['GES_descripcion_3'] = df_merged_tips.get('Calif_3', '')
            else:
                st.warning("⚠️ No se pudo realizar el cruce de tipificaciones. Revisa la columna 'COD_VICIDIAL'.")

            # 6. Cruce Campañas (Manejo de error 'ORIGINAL')
            if df_camps is not None and 'ORIGINAL' in df_camps.columns:
                df_input['campaign_id'] = df_input['campaign_id'].astype(str)
                df_camps['ORIGINAL'] = df_camps['ORIGINAL'].astype(str)
                df_merged_camps = pd.merge(df_input[['campaign_id']], df_camps, left_on='campaign_id', right_on='ORIGINAL', how='left')
                res['GES_nombre_campana_gestion'] = df_merged_camps.get('FINAL', '')
                res['GES_dato_variable_27'] = df_merged_camps.get('GES_dato_variable_27', '')
            else:
                st.warning("⚠️ No se pudo realizar el cruce de campañas. Revisa la columna 'ORIGINAL'.")

            # 7. Lógica de Ventas
            es_venta = res.get('GES_descripcion_3', '').astype(str).str.upper().str.contains('VENTA')
            res['GES_dato_variable_05'] = ""
            res['GES_dato_variable_26'] = ""
            
            if 'BI' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns:
                res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']

            # --- TRANSFORMACIÓN FINAL A MAYÚSCULAS ---
            res = res.astype(str).apply(lambda x: x.str.upper())
            res = res.replace('NAN', '').replace('NONE', '')

            st.success("¡Resultante procesada exitosamente!")
            st.dataframe(res.head())

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Excel Final (MAYÚSCULAS)",
                data=output.getvalue(),
                file_name="Resultante_BCI_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico crítico: {e}")
