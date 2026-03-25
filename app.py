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

# INTERFAZ RECAALL PRINCIPAL
col_titulo, col_logout = st.columns([4, 1])
with col_titulo:
    st.markdown("<h1>RECAALL CONTACT CENTER</h1>", unsafe_allow_html=True)
    st.markdown("### Generador de Resultantes BCI")
with col_logout:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

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

            # --- PASO 2: Datos de Gestión ---
            status.markdown("**40%** - Calculando tiempos de gestión y formateando nombres...")
            res['GES_nombre_cliente'] = (df_input.get('first_name', pd.Series(dtype=str)).astype(str).replace('nan', '') + " " + df_input.get('last_name', pd.Series(dtype=str)).astype(str).replace('nan', '')).str.strip()
            res['GES_estado_cliente'] = "T"
            res['FDL_identificador_documento'] = df_input.get('lead_id', '')
            res['FDL_referencia_documento'] = df_input.get('length_in_sec', pd.Series(dtype=float)).apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")
            res['FDL_username_originador'] = df_input.get('full_name', '')
            bar.progress(40)

            # --- PASO 3: Cruces de Tipificaciones ---
            status.markdown("**65%** - Realizando cruces de tipificaciones...")
            res['GES_descripcion_1'], res['GES_descripcion_2'], res['GES_descripcion_3'] = "", "", ""
            if df_tips is not None and not df_tips.empty and 'COD_VICIDIAL' in df_tips.columns and 'status' in df_input.columns:
                df_input['status_clean'] = df_input['status'].fillna('').astype(str).str.strip().str.upper()
                df_tips['COD_clean'] = df_tips['COD_VICIDIAL'].fillna('').astype(str).str.strip().str.upper()
                
                df_tips_unique = df_tips.drop_duplicates(subset=['COD_clean'])
                m_tips = pd.merge(df_input[['status_clean']], df_tips_unique, left_on='status_clean', right_on='COD_clean', how='left')
                
                res['GES_descripcion_1'] = m_tips['Calif_1'].fillna('').values if 'Calif_1' in m_tips.columns else ""
                res['GES_descripcion_2'] = m_tips['Calif_2'].fillna('').values if 'Calif_2' in m_tips.columns else ""
                res['GES_descripcion_3'] = m_tips['Calif_3'].fillna('').values if 'Calif_3' in m_tips.columns else ""
            bar.progress(65)

            # --- PASO 4: Cruces de Campañas e inyección MMYYYY ---
            status.markdown("**80%** - Realizando cruces de campañas e inyectando mes/año...")
            res['GES_nombre_campana_gestion'], res['GES_dato_variable_27'] = "", ""
            
            if df_camps is not None and not df_camps.empty and 'ORIGINAL' in df_camps.columns and 'campaign_id' in df_input.columns:
                df_input['camp_clean'] = df_input['campaign_id'].fillna('').astype(str).str.strip().str.upper()
                df_camps['ORIGINAL_clean'] = df_camps['ORIGINAL'].fillna('').astype(str).str.strip().str.upper()
                
                df_camps_unique = df_camps.drop_duplicates(subset=['ORIGINAL_clean'])
                m_camps = pd.merge(df_input[['camp_clean']], df_camps_unique, left_on='camp_clean', right_on='ORIGINAL_clean', how='left')
                
                res['GES_nombre_campana_gestion'] = m_camps['FINAL'].fillna('').values if 'FINAL' in m_camps.columns else ""
                
                if 'GES_dato_variable_27' in m_camps.columns:
                    base_var_27 = m_camps['GES_dato_variable_27'].fillna('').astype(str).values
                    fechas_mmyyyy = call_dt.dt.strftime('%m%Y').fillna('').values
                    res['GES_dato_variable_27'] = [val.replace('MMYYYY', fecha) if 'MMYYYY' in val else val for val, fecha in zip(base_var_27, fechas_mmyyyy)]
            bar.progress(80)

            # --- PASO 5: Lógica Final, Ordenamiento y Formato ---
            status.markdown("**90%** - Ordenando reporte y calculando métricas de efectividad...")
            es_venta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.strip().str.startswith('VENTA')
            res['GES_dato_variable_05'], res['GES_dato_variable_26'], res['GES_dato_variable_19'] = "", "", ""
            if 'BI' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_05'] = df_input.loc[es_venta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_venta, 'GES_dato_variable_26'] = df_input.loc[es_venta, 'BK']

            res = res.sort_values(by=['GES_nombre_campana_gestion', 'GES_hora_min_creacion'], ascending=[True, True])
            res = res.reset_index(drop=True)

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
            res_upper = res.astype(str).apply(lambda x: x.str.upper()).replace(['NAN', 'NONE', '<NA>'], '')

            columnas_titulo = ['GES_username_recurso', 'FDL_username_originador', 'GES_descripcion_1', 'GES_descripcion_2', 'GES_descripcion_3']
            for col in columnas_titulo:
                res_upper[col] = res[col].astype(str).str.title().replace('Nan', '').replace('None', '')
            
            res = res_upper
            bar.progress(100)
            status.success("✅ **100%** - ¡Proceso completado con éxito!")
            time.sleep(0.5)

            # --- MÉTRICAS Y GRÁFICOS EJECUTIVOS ---
            st.markdown("---")
            st.markdown("### 📊 Panel de Desempeño y Ventas")
            
            df_ventas = res[res['GES_descripcion_3'].astype(str).str.upper().str.strip().str.startswith('VENTA')]
            
            if not df_ventas.empty:
                col_c1, col_c2 = st.columns(2)
                
                # Gráfico 1: Ventas por Campaña
                with col_c1:
                    st.write("**Total Ventas por Campaña**")
                    conteo_ventas = df_ventas.groupby('GES_nombre_campana_gestion').size().reset_index(name='Ventas')
                    base_c1 = alt.Chart(conteo_ventas).encode(x=alt.X('GES_nombre_campana_gestion:N', title='Campaña'))
                    barras_c1 = base_c1.mark_bar(color="#FF9800", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y('Ventas:Q', title='Cantidad'))
                    texto_c1 = base_c1.mark_text(align='center', baseline='line-top', dy=-15, color='#333333', fontSize=12, fontWeight='bold').encode(text=alt.Text('Ventas:Q'), y=alt.Y('Ventas:Q'))
                    st.altair_chart((barras_c1 + texto_c1).properties(height=250), use_container_width=True)

                # Gráfico 2: Ventas por Hora
                with col_c2:
                    st.write("**Ventas por Hora General**")
                    df_ventas_h = df_ventas.copy()
                    df_ventas_h['Hora'] = df_ventas_h['GES_hora_min_creacion'].astype(str).str.split(':').str[0].astype(int)
                    conteo_horas = df_ventas_h.groupby('Hora').size().reset_index(name='Ventas_Hora').sort_values('Hora')
                    base_c2 = alt.Chart(conteo_horas).encode(x=alt.X('Hora:O', title='Hora (H)'))
                    barras_c2 = base_c2.mark_bar(color="#003366", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y('Ventas_Hora:Q', title='Cantidad'))
                    texto_c2 = base_c2.mark_text(align='center', baseline='line-top', dy=-15, color='#333333', fontSize=12, fontWeight='bold').encode(text=alt.Text('Ventas_Hora:Q'), y=alt.Y('Ventas_Hora:Q'))
                    st.altair_chart((barras_c2 + texto_c2).properties(height=250), use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                col_c3, col_c4 = st.columns(2)

                # Gráfico 3: Ventas por Hora POR CAMPAÑA
                with col_c3:
                    st.write("**Ventas por Hora según Campaña**")
                    conteo_hc = df_ventas_h.groupby(['Hora', 'GES_nombre_campana_gestion']).size().reset_index(name='Ventas')
                    chart3 = alt.Chart(conteo_hc).mark_bar().encode(
                        x=alt.X('Hora:O', title='Hora del Día'),
                        y=alt.Y('Ventas:Q', title='Ventas'),
                        color=alt.Color('GES_nombre_campana_gestion:N', title='Campaña', scale=alt.Scale(scheme='set2')),
                        tooltip=['Hora', 'GES_nombre_campana_gestion', 'Ventas']
                    ).properties(height=300)
                    st.altair_chart(chart3, use_container_width=True)

                # Gráfico 4: Efectividad por Ejecutivo
                with col_c4:
                    st.write("**Efectividad por Ejecutivo (Ventas / Total Llamados)**")
                    llamados_ejecutivo = res.groupby('GES_username_recurso').size().reset_index(name='Total_Llamados')
                    ventas_ejecutivo = df_ventas.groupby('GES_username_recurso').size().reset_index(name='Total_Ventas')
                    
                    efectividad = pd.merge(llamados_ejecutivo, ventas_ejecutivo, on='GES_username_recurso', how='left').fillna(0)
                    efectividad['Efectividad (%)'] = ((efectividad['Total_Ventas'] / efectividad['Total_Llamados']) * 100).round(1)
                    efectividad = efectividad.sort_values('Efectividad (%)', ascending=False)
                    
                    efectividad_activa = efectividad[efectividad['Total_Ventas'] > 0]
                    
                    base_c4 = alt.Chart(efectividad_activa).encode(
                        x=alt.X('Efectividad (%):Q', title='Efectividad (%)'),
                        y=alt.Y('GES_username_recurso:N', title='', sort='-x')
                    )
                    barras_c4 = base_c4.mark_bar(color="#2ca02c", cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                    texto_c4 = base_c4.mark_text(align='left', baseline='middle', dx=3, color='#333333', fontSize=11, fontWeight='bold').encode(
                        text=alt.Text('Efectividad (%):Q', format='.1f')
                    )
                    
                    alto_grafico = max(250, len(efectividad_activa) * 25)
                    st.altair_chart((barras_c4 + texto_c4).properties(height=alto_grafico), use_container_width=True)

            else:
                st.info("No se registraron ventas reales en este reporte para generar gráficos.")

            st.markdown("---")

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
                label="📥 DESCARGAR REPORTE RECAALL ORDENADO",
                data=output.getvalue(),
                file_name="RECAALL_BCI_FINAL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico durante el proceso: {e}")
