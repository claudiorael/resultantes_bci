import streamlit as st, pandas as pd, re, time, altair as alt
from io import BytesIO
from datetime import timedelta
from openpyxl.styles import Font

# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO RECAALL
st.set_page_config(page_title="Recaall | Gestión BCI", layout="wide", page_icon="📈")
st.markdown("""<style>
    .main { background-color: #f4f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #003366; color: white; font-weight: 600; border: none; }
    .stButton>button:hover { background-color: #004080; color: white; }
    .recaall-card { padding: 25px; border-radius: 12px; background-color: white; border-left: 5px solid #003366; margin-bottom: 20px; }
    h1 { color: #003366; font-weight: 700; margin-bottom: 0; }
    h3 { color: #555555; margin-top: 0; }
    .stProgress > div > div > div > div { background-color: #FF7F00 !important; }
    [data-testid="stFileUploadDropzone"] { min-height: 80px !important; padding: 15px !important; }
    a.header-anchor { display: none !important; }
    </style>""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN Y SEGURIDAD ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if not st.session_state['autenticado']:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="recaall-card" style="text-align: center;"><h1>RECAALL</h1><h4 style="color: #555;">Acceso Restringido - Plataforma BCI</h4><hr>', unsafe_allow_html=True)
        clave = st.text_input("🔒 Ingrese la clave corporativa:", type="password")
        if st.button("Iniciar Sesión"):
            if clave == "Recaall2026": # AQUÍ PUEDES CAMBIAR LA CONTRASEÑA
                st.session_state['autenticado'] = True
                st.rerun()
            else: st.error("❌ Clave incorrecta. Intente nuevamente.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# --- A PARTIR DE AQUÍ COMIENZA LA APLICACIÓN (SOLO SI ESTÁ LOGUEADO) ---
# =====================================================================

def limpiar_rut(rut):
    return re.sub(r'[^0-9kK]', '', str(rut)).upper() if pd.notna(rut) and rut != '' else ""

@st.cache_data
def load_masters():
    t, c = None, None
    for enc in ['utf-8', 'latin1']:
        try: t = pd.read_csv('tipificaciones.csv', sep=None, engine='python', encoding=enc); break
        except: pass
    if t is None:
        try: t = pd.read_excel('tipificaciones.xlsx')
        except: pass
    
    for enc in ['utf-8', 'latin1']:
        try: c = pd.read_csv('campanas.csv', sep=None, engine='python', encoding=enc); break
        except: pass
    if c is None:
        try: c = pd.read_excel('campanas.xlsx')
        except: pass
        
    if t is not None: t.columns = t.columns.str.strip()
    if c is not None: c.columns = c.columns.str.strip()
    return t, c

df_tips, df_camps = load_masters()

# INTERFAZ RECAALL PRINCIPAL
c_tit, c_log = st.columns([4, 1])
with c_tit: st.markdown("<h1>RECAALL CONTACT CENTER</h1><h3>Generador de Resultantes BCI</h3>", unsafe_allow_html=True)
with c_log:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False; st.rerun()
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
            bar = st.progress(0); status = st.empty(); res = pd.DataFrame()
            
            # --- PASO 1 y 2: Identificadores y Gestión ---
            status.markdown("**20%** - Estructurando base e identificadores...")
            res['GES_nro_contacto'] = df_input.get('lead_id', '')
            cdt = pd.to_datetime(df_input.get('call_date', pd.Series(dtype='datetime64[ns]')))
            res['GES_fecha_creacion'] = cdt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = cdt.dt.strftime('%H:%M:%S')
            res['GES_username_recurso'] = df_input.get('full_name', '')
            res['GES_ani'] = df_input.get('phone_number_dialed', '')
            res['GES_id_cliente'] = df_input.get('vendor_lead_code', pd.Series(dtype=str)).apply(limpiar_rut)
            bar.progress(20)

            status.markdown("**40%** - Calculando tiempos y formateando nombres...")
            fn = df_input.get('first_name', pd.Series(dtype=str)).astype(str).replace('nan', '')
            ln = df_input.get('last_name', pd.Series(dtype=str)).astype(str).replace('nan', '')
            res['GES_nombre_cliente'] = (fn + " " + ln).str.strip()
            res['GES_estado_cliente'] = "T"
            res['FDL_identificador_documento'] = df_input.get('lead_id', '')
            t_sec = df_input.get('length_in_sec', pd.Series(dtype=float))
            res['FDL_referencia_documento'] = t_sec.apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")
            res['FDL_username_originador'] = df_input.get('full_name', '')
            bar.progress(40)

            # --- PASO 3: Cruce Tipificaciones ---
            status.markdown("**65%** - Realizando cruces de tipificaciones...")
            res['GES_descripcion_1'], res['GES_descripcion_2'], res['GES_descripcion_3'] = "", "", ""
            if df_tips is not None and 'COD_VICIDIAL' in df_tips.columns and 'status' in df_input.columns:
                df_input['s_cln'] = df_input['status'].fillna('').astype(str).str.strip().str.upper()
                df_tips['c_cln'] = df_tips['COD_VICIDIAL'].fillna('').astype(str).str.strip().str.upper()
                m_tips = pd.merge(df_input[['s_cln']], df_tips.drop_duplicates(subset=['c_cln']), left_on='s_cln', right_on='c_cln', how='left')
                res['GES_descripcion_1'] = m_tips['Calif_1'].fillna('').values if 'Calif_1' in m_tips.columns else ""
                res['GES_descripcion_2'] = m_tips['Calif_2'].fillna('').values if 'Calif_2' in m_tips.columns else ""
                res['GES_descripcion_3'] = m_tips['Calif_3'].fillna('').values if 'Calif_3' in m_tips.columns else ""
            bar.progress(65)

            # --- PASO 4: Cruce Campañas ---
            status.markdown("**80%** - Realizando cruces de campañas e inyectando mes/año...")
            res['GES_nombre_campana_gestion'], res['GES_dato_variable_27'] = "", ""
            if df_camps is not None and 'ORIGINAL' in df_camps.columns and 'campaign_id' in df_input.columns:
                df_input['c_cln'] = df_input['campaign_id'].fillna('').astype(str).str.strip().str.upper()
                df_camps['o_cln'] = df_camps['ORIGINAL'].fillna('').astype(str).str.strip().str.upper()
                m_camps = pd.merge(df_input[['c_cln']], df_camps.drop_duplicates(subset=['o_cln']), left_on='c_cln', right_on='o_cln', how='left')
                res['GES_nombre_campana_gestion'] = m_camps['FINAL'].fillna('').values if 'FINAL' in m_camps.columns else ""
                if 'GES_dato_variable_27' in m_camps.columns:
                    b27 = m_camps['GES_dato_variable_27'].fillna('').astype(str).values
                    fm = cdt.dt.strftime('%m%Y').fillna('').values
                    res['GES_dato_variable_27'] = [v.replace('MMYYYY', f) if 'MMYYYY' in v else v for v, f in zip(b27, fm)]
            bar.progress(80)

            # --- PASO 5: Lógica Final, Formato y Reordenamiento ---
            status.markdown("**90%** - Ordenando reporte y calculando métricas de efectividad...")
            es_vta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.strip().str.startswith('VENTA')
            res['GES_dato_variable_05'], res['GES_dato_variable_26'], res['GES_dato_variable_19'] = "", "", ""
            if 'BI' in df_input.columns: res.loc[es_vta, 'GES_dato_variable_05'] = df_input.loc[es_vta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_vta, 'GES_dato_variable_26'] = df_input.loc[es_vta, 'BK']

            res = res.sort_values(by=['GES_nombre_campana_gestion', 'GES_hora_min_creacion']).reset_index(drop=True)
            cols = ['GES_nro_contacto', 'GES_fecha_creacion', 'GES_hora_min_creacion', 'GES_username_recurso', 'GES_ani', 'GES_id_cliente', 'GES_nombre_cliente', 'GES_estado_cliente', 'FDL_identificador_documento', 'FDL_referencia_documento', 'FDL_username_originador', 'GES_descripcion_1', 'GES_descripcion_2', 'GES_descripcion_3', 'GES_nombre_campana_gestion', 'GES_dato_variable_05', 'GES_dato_variable_26', 'GES_dato_variable_27', 'GES_dato_variable_19']
            res = res.reindex(columns=cols)
            
            res_upper = res.astype(str).apply(lambda x: x.str.upper()).replace(['NAN', 'NONE', '<NA>'], '')
            c_titulos = ['GES_username_recurso', 'FDL_username_originador', 'GES_descripcion_1', 'GES_descripcion_2', 'GES_descripcion_3']
            for c in c_titulos: res_upper[c] = res[c].astype(str).str.title().replace('Nan', '').replace('None', '')
            res = res_upper
            
            bar.progress(100); status.success("✅ **100%** - ¡Proceso completado con éxito!"); time.sleep(0.5)

            # --- MÉTRICAS Y GRÁFICOS EJECUTIVOS ---
            st.markdown("---")
            st.markdown("### 📊 Panel de Desempeño y Ventas")
            df_ventas = res[res['GES_descripcion_3'].astype(str).str.upper().str.strip().str.startswith('VENTA')]
            
            if not df_ventas.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Total Ventas por Campaña**")
                    cv = df_ventas.groupby('GES_nombre_campana_gestion').size().reset_index(name='Ventas')
                    b1 = alt.Chart(cv).encode(x=alt.X('GES_nombre_campana_gestion:N', title='Campaña'))
                    st.altair_chart((b1.mark_bar(color="#FF9800", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y('Ventas:Q', title='Cantidad')) + b1.mark_text(align='center', baseline='line-top', dy=-15, color='#333333', fontSize=12, fontWeight='bold').encode(text=alt.Text('Ventas:Q'), y=alt.Y('Ventas:Q'))).properties(height=250), use_container_width=True)
                with c2:
                    st.write("**Ventas por Hora General**")
                    dvh = df_ventas.copy()
                    dvh['Hora'] = dvh['GES_hora_min_creacion'].astype(str).str.split(':').str[0].astype(int)
                    ch = dvh.groupby('Hora').size().reset_index(name='Ventas_Hora').sort_values('Hora')
                    b2 = alt.Chart(ch).encode(x=alt.X('Hora:O', title='Hora (H)'))
                    st.altair_chart((b2.mark_bar(color="#003366", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y=alt.Y('Ventas_Hora:Q', title='Cantidad')) + b2.mark_text(align='center', baseline='line-top', dy=-15, color='#333333', fontSize=12, fontWeight='bold').encode(text=alt.Text('Ventas_Hora:Q'), y=alt.Y('Ventas_Hora:Q'))).properties(height=250), use_container_width=True)
                
                c3, c4 = st.columns(2)
                with c3:
                    st.write("**Ventas por Hora según Campaña**")
                    chc = dvh.groupby(['Hora', 'GES_nombre_campana_gestion']).size().reset_index(name='Ventas')
                    st.altair_chart(alt.Chart(chc).mark_bar().encode(x=alt.X('Hora:O', title='Hora del Día'), y=alt.Y('Ventas:Q', title='Ventas'), color=alt.Color('GES_nombre_campana_gestion:N', title='Campaña', scale=alt.Scale(scheme='set2')), tooltip=['Hora', 'GES_nombre_campana_gestion', 'Ventas']).properties(height=300), use_container_width=True)
                with c4:
                    st.write("**Efectividad por Ejecutivo (Ventas / Llamados)**")
                    lle = res.groupby('GES_username_recurso').size().reset_index(name='Llamados')
                    vte = df_ventas.groupby('GES_username_recurso').size().reset_index(name='Ventas')
                    ef = pd.merge(lle, vte, on='GES_username_recurso', how='left').fillna(0)
                    ef['Efectividad'] = ((ef['Ventas'] / ef['Llamados']) * 100).round(1)
                    efa = ef[ef['Ventas'] > 0].sort_values('Efectividad', ascending=False)
                    b4 = alt.Chart(efa).encode(x=alt.X('Efectividad:Q', title='Efectividad (%)'), y=alt.Y('GES_username_recurso:N', title='', sort='-x'))
                    st.altair_chart((b4.mark_bar(color="#2ca02c", cornerRadiusTopRight=4, cornerRadiusBottomRight=4) + b4.mark_text(align='left', baseline='middle', dx=3, color='#333333', fontSize=11, fontWeight='bold').encode(text=alt.Text('Efectividad:Q', format='.1f'))).properties(height=max(250, len(efa)*25)), use_container_width=True)
            else: st.info("No se registraron ventas reales en este reporte para generar gráficos.")
            
            # --- PASO 6: Generación del Excel ---
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as w:
                res.to_excel(w, index=False, sheet_name='Resultante BCI')
                for r in w.sheets['Resultante BCI'].iter_rows():
                    for c in r: c.font = Font(name='Calibri', size=9)
            st.markdown("---")
            st.download_button("📥 DESCARGAR REPORTE RECAALL ORDENADO", data=out.getvalue(), file_name="RECAALL_BCI_FINAL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e: st.error(f"Error técnico durante el proceso: {e}")
