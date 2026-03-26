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
    .recaall-card { padding: 25px; border-radius: 12px; background-color: white; border-left: 5px solid #003366; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #003366; font-weight: 700; margin-bottom: 0; }
    h3 { color: #555555; margin-top: 0; }
    .stProgress > div > div > div > div { background-color: #FF7F00 !important; }
    [data-testid="stFileUploadDropzone"] { min-height: 80px !important; padding: 15px !important; }
    a.header-anchor { display: none !important; }
    </style>""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if not st.session_state['autenticado']:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="recaall-card" style="text-align: center;"><h1>RECAALL</h1><h4 style="color: #555;">Acceso Restringido - Plataforma BCI</h4><hr>', unsafe_allow_html=True)
        clave = st.text_input("🔒 Ingrese la clave corporativa:", type="password")
        if st.button("Iniciar Sesión"):
            if clave == "Recaall2026":
                st.session_state['autenticado'] = True; st.rerun()
            else: st.error("❌ Clave incorrecta.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- FUNCIONES DE APOYO ---
def limpiar_rut(rut):
    return re.sub(r'[^0-9kK]', '', str(rut)).upper() if pd.notna(rut) and rut != '' else ""

@st.cache_data
def load_masters():
    t, c = None, None
    for f, name in [('tipificaciones', 't'), ('campanas', 'c')]:
        for ext in ['.csv', '.xlsx']:
            try:
                path = f + ext
                if ext == '.csv': 
                    data = pd.read_csv(path, sep=None, engine='python', encoding='latin1')
                else: 
                    data = pd.read_excel(path)
                data.columns = data.columns.str.strip()
                if name == 't': t = data
                else: c = data
                break
            except: pass
    return t, c

df_tips, df_camps = load_masters()

# --- INTERFAZ PRINCIPAL ---
c_tit, c_log = st.columns([4, 1])
with c_tit: st.markdown("<h1>RECAALL CONTACT CENTER</h1><h3>Generador de Resultantes BCI</h3>", unsafe_allow_html=True)
with c_log:
    st.write("<br>", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"): st.session_state['autenticado'] = False; st.rerun()
st.write("---")

col1, col2 = st.columns([1, 2.5])
with col1:
    st.markdown("#### ⚙️ Configuración")
    if df_tips is not None: st.success("✅ Tipificaciones OK")
    else: st.error("❌ Tipificaciones no detectadas")
    if df_camps is not None: st.success("✅ Campañas OK")
    else: st.error("❌ Campañas no detectadas")

with col2:
    # Acepta .txt, .csv y .xlsx
    file = st.file_uploader("📥 Subir reporte Vicidial", type=["xlsx", "csv", "txt"])

if file:
    try:
        if file.name.endswith('xlsx'): df_input = pd.read_excel(file)
        else: df_input = pd.read_csv(file, sep=None, engine='python', encoding='latin1')
        df_input.columns = df_input.columns.str.strip()
        st.info(f"📋 Registros cargados: {len(df_input)}")
        
        if st.button("🚀 PROCESAR"):
            bar = st.progress(0); status = st.empty(); res = pd.DataFrame()
            
            # PASO 1 y 2: Identificadores
            status.markdown("**20%** - Estructurando base..."); bar.progress(20)
            res['GES_nro_contacto'] = df_input.get('lead_id', '')
            cdt = pd.to_datetime(df_input.get('call_date', pd.Series(dtype='datetime64[ns]')))
            res['GES_fecha_creacion'] = cdt.dt.strftime('%d/%m/%Y')
            res['GES_hora_min_creacion'] = cdt.dt.strftime('%H:%M:%S')
            res['GES_username_recurso'] = df_input.get('full_name', '')
            res['GES_ani'] = df_input.get('phone_number_dialed', '')
            res['GES_id_cliente'] = df_input.get('vendor_lead_code', pd.Series(dtype=str)).apply(limpiar_rut)
            
            # Tiempos y Nombres
            fn = df_input.get('first_name', pd.Series(dtype=str)).astype(str).replace('nan', '')
            ln = df_input.get('last_name', pd.Series(dtype=str)).astype(str).replace('nan', '')
            res['GES_nombre_cliente'] = (fn + " " + ln).str.strip()
            res['GES_estado_cliente'] = "T"
            res['FDL_identificador_documento'] = df_input.get('lead_id', '')
            t_sec = df_input.get('length_in_sec', pd.Series(dtype=float))
            res['FDL_referencia_documento'] = t_sec.apply(lambda x: str(timedelta(seconds=int(x))) if pd.notnull(x) else "00:00:00")
            res['FDL_username_originador'] = df_input.get('full_name', '')
            
            # PASO 3: Tipificaciones
            status.markdown("**65%** - Cruzando tipificaciones..."); bar.progress(65)
            if df_tips is not None:
                df_input['s_cln'] = df_input['status'].fillna('').astype(str).str.strip().str.upper()
                df_tips['c_cln'] = df_tips['COD_VICIDIAL'].fillna('').astype(str).str.strip().str.upper()
                m_tips = pd.merge(df_input[['s_cln']], df_tips.drop_duplicates('c_cln'), left_on='s_cln', right_on='c_cln', how='left')
                res['GES_descripcion_1'] = m_tips['Calif_1'].fillna('').values
                res['GES_descripcion_2'] = m_tips['Calif_2'].fillna('').values
                res['GES_descripcion_3'] = m_tips['Calif_3'].fillna('').values

            # PASO 4: Campañas y MMYYYY
            status.markdown("**80%** - Cruzando campañas..."); bar.progress(80)
            if df_camps is not None:
                df_input['c_cln'] = df_input['campaign_id'].fillna('').astype(str).str.strip().str.upper()
                df_camps['o_cln'] = df_camps['ORIGINAL'].fillna('').astype(str).str.strip().str.upper()
                m_camps = pd.merge(df_input[['c_cln']], df_camps.drop_duplicates('o_cln'), left_on='c_cln', right_on='o_cln', how='left')
                res['GES_nombre_campana_gestion'] = m_camps['FINAL'].fillna('').values
                if 'GES_dato_variable_27' in m_camps.columns:
                    b27 = m_camps['GES_dato_variable_27'].fillna('').astype(str).values
                    fm = cdt.dt.strftime('%m%Y').fillna('').values
                    res['GES_dato_variable_27'] = [v.replace('MMYYYY', f) if 'MMYYYY' in v else v for v, f in zip(b27, fm)]

            # PASO 5: Formato y Orden
            status.markdown("**95%** - Aplicando formatos finales..."); bar.progress(95)
            es_vta = res['GES_descripcion_3'].fillna('').astype(str).str.upper().str.strip().str.startswith('VENTA')
            res['GES_dato_variable_05'], res['GES_dato_variable_26'], res['GES_dato_variable_19'] = "", "", ""
            if 'BI' in df_input.columns: res.loc[es_vta, 'GES_dato_variable_05'] = df_input.loc[es_vta, 'BI']
            if 'BK' in df_input.columns: res.loc[es_vta, 'GES_dato_variable_26'] = df_input.loc[es_vta, 'BK']

            res = res.sort_values(by=['GES_nombre_campana_gestion', 'GES_hora_min_creacion']).reset_index(drop=True)
            cols = ['GES_nro_contacto', 'GES_fecha_creacion', 'GES_hora_min_creacion', 'GES_username_recurso', 'GES_ani', 'GES_id_cliente', 'GES_nombre_cliente', 'GES_estado_cliente', 'FDL_identificador_documento', 'FDL_referencia_documento', 'FDL_username_originador', 'GES_descripcion_1', 'GES_descripcion_2', 'GES_descripcion_3', 'GES_nombre_campana_gestion', 'GES_dato_variable_05', 'GES_dato_variable_26', 'GES_dato_variable_27', 'GES_dato_variable_19']
            res = res.reindex(columns=cols).astype(str).apply(lambda x: x.str.upper()).replace(['NAN', 'NONE', '<NA>'], '')
            
            c_tit = ['GES_username_recurso', 'FDL_username_originador', 'GES_descripcion_1', 'GES_descripcion_2', 'GES_descripcion_3']
            for c in c_tit: res[c] = res[c].str.title()
            
            bar.progress(100); status.success("✅ ¡Proceso completado!"); time.sleep(0.5)

            # --- PANEL DE GRÁFICOS ---
            st.markdown("---")
            st.markdown("### 📊 Panel de Desempeño")
            dv = res[res['GES_descripcion_3'].str.upper().str.startswith('VENTA')]
            
            if not dv.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Ventas por Campaña**")
                    cv = dv.groupby('GES_nombre_campana_gestion').size().reset_index(name='V')
                    ch1 = alt.Chart(cv).encode(x='GES_nombre_campana_gestion:N')
                    st.altair_chart((ch1.mark_bar(color="#FF9800", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y='V:Q') + ch1.mark_text(align='center', baseline='line-top', dy=-15, fontWeight='bold').encode(text='V:Q', y='V:Q')).properties(height=250), use_container_width=True)
                with c2:
                    st.write("**Ventas por Hora**")
                    dv['H'] = dv['GES_hora_min_creacion'].str.split(':').str[0].astype(int)
                    ch = dv.groupby('H').size().reset_index(name='V').sort_values('H')
                    ch2 = alt.Chart(ch).encode(x='H:O')
                    st.altair_chart((ch2.mark_bar(color="#003366", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(y='V:Q') + ch2.mark_text(align='center', baseline='line-top', dy=-15, fontWeight='bold').encode(text='V:Q', y='V:Q')).properties(height=250), use_container_width=True)
                
                c3, c4 = st.columns(2)
                with c3:
                    st.write("**Ventas Hora/Campaña**")
                    chc = dv.groupby(['H', 'GES_nombre_campana_gestion']).size().reset_index(name='V')
                    st.altair_chart(alt.Chart(chc).mark_bar().encode(x='H:O', y='V:Q', color='GES_nombre_campana_gestion:N').properties(height=300), use_container_width=True)
                with c4:
                    st.write("**Efectividad por Ejecutivo (%)**")
                    lle = res.groupby('GES_username_recurso').size().reset_index(name='L')
                    vte = dv.groupby('GES_username_recurso').size().reset_index(name='V')
                    ef = pd.merge(lle, vte, on='GES_username_recurso', how='left').fillna(0)
                    ef['E%'] = ((ef['V'] / ef['L']) * 100).round(1)
                    efa = ef[ef['V'] > 0].sort_values('E%', ascending=False)
                    b4 = alt.Chart(efa).encode(x='E%:Q', y=alt.Y('GES_username_recurso:N', sort='-x'))
                    st.altair_chart((b4.mark_bar(color="#2ca02c") + b4.mark_text(align='left', dx=3, fontWeight='bold').encode(text='E%:Q')).properties(height=max(250, len(efa)*20)), use_container_width=True)
            else: st.info("No hay ventas reales para graficar.")
            
            # EXCEL
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as w:
                res.to_excel(w, index=False, sheet_name='BCI')
                for r in w.sheets['BCI'].iter_rows():
                    for c in r: c.font = Font(name='Calibri', size=9)
            st.download_button("📥 DESCARGAR RESULTANTE", data=out.getvalue(), file_name="RECAALL_BCI.xlsx")

    except Exception as e: st.error(f"Error: {e}")
