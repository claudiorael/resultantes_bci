import streamlit as st
import pandas as pd
from PIL import Image

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="RECAALL CONTACT CENTER - Generador",
    layout="wide" # Diseño ancho para que quepa la tabla de datos
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    /* Título y Cabecera */
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .main-title {
        color: #333;
        margin: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    .chain-icon {
        margin-left: 10px;
        color: #555;
        font-size: 20px;
    }
    .subtitle {
        margin-top: -5px;
        color: #555;
        font-weight: 400;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Caja de Configuración (Panel Izquierdo) */
    .config-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        background-color: #f9f9f9;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .config-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .gear-icon {
        color: #003366;
        font-size: 24px;
    }
    .config-title {
        color: #003366;
        margin: 0 0 0 10px;
        font-weight: 400;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .verificacion-text {
        margin-bottom: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .status-box {
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .red-status {
        border: 1px solid #ff4d4d;
        background-color: #ffeaea;
        color: #ff4d4d;
    }
    .green-status {
        border: 1px solid #4CAF50;
        background-color: #e8f5e9;
        color: #4CAF50;
    }

    /* Zona de File Uploader (Panel Derecho) */
    .file-uploader-text {
        margin-bottom: 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .custom-uploader {
        border: 2px dashed #ddd;
        border-radius: 8px;
        padding: 30px;
        text-align: center;
        color: #777;
        background-color: #f0f4f8;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .upload-icon {
        font-size: 40px;
        color: #bbb;
    }
    .attached-file {
        display: flex;
        align-items: center;
        justify-content: start;
        margin-top: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .file-icon {
        font-size: 20px;
        color: #bbb;
    }

    /* Mensaje Info (Azul) */
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        border-radius: 4px;
        padding: 10px;
        display: flex;
        align-items: center;
        justify-content: start;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-top: 15px;
    }
    .clipboard-icon {
        margin-right: 10px;
        font-size: 20px;
    }

    /* Botón PROCESAR (Azul Oscuro) */
    .procesar-btn {
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        background-color: #003366;
        color: white;
        font-weight: 700;
        font-size: 16px;
        cursor: pointer;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-top: 15px;
    }

    /* Línea Horizontal Prominente */
    .divider-prominent {
        border: 3px solid #003366;
        border-radius: 2px;
        margin-top: 25px;
        margin-bottom: 25px;
    }

    /* Mensaje de Éxito (Verde) */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        border-radius: 4px;
        padding: 10px;
        display: flex;
        align-items: center;
        justify-content: start;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .check-icon {
        margin-right: 10px;
        font-size: 20px;
    }

    /* Ocultar anclas de cabecera predeterminadas de Streamlit */
    a.header-anchor { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. BRANDING DE CABECERA (Arriba a la Izquierda)
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">RECAALL CONTACT CENTER</h1>
        <span class="chain-icon">🔗</span>
    </div>
    <h3 class="subtitle">Generador de Resultantes BCI</h3>
    """, unsafe_allow_html=True)

# 3. COLOCACIÓN DEL LOGO CENTRAL
# Aquí se ha eliminado el carácter extraño (paréntesis) que estaba antes.
# Usamos columnas para centrar el logo oficial proporcionado (image_6.png).
st.markdown("<br>", unsafe_allow_html=True)
col_l, col_center, col_r = st.columns([1, 2, 1])
with col_center:
    # Se carga la imagen image_6.png (el logo completo).
    # Asegúrate de tener este archivo en la misma carpeta que el app.py.
    logo_image = Image.open('image_6.png')
    st.image(logo_image, width=320, use_column_width=False, output_format='PNG')

# 4. COLUMNAS PRINCIPALES (Estado y Subida)
col_status, col_upload = st.columns([1, 2.5])

# --- Panel Izquierdo: Configuración/Estado ---
with col_status:
    st.markdown("""
        <div class="config-card">
            <div class="config-header">
                <span class="gear-icon">⚙️</span>
                <h2 class="config-title">Configuration</h2>
            </div>
            <p class="verificacion-text">Verificando archivos maestros:</p>
            <div class="status-box red-status">
                ❌ Tipificaciones no detectadas
            </div>
            <div class="status-box green-status">
                ✅ Campañas OK
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Panel Derecho: File Uploader ---
with col_upload:
    st.markdown("<p class='file-uploader-text'>Subir reporte Vicidial para procesamiento</p>", unsafe_allow_html=True)
    # Se recrea visualmente la caja de subida personalizada de la imagen
    st.markdown("""
        <div class="custom-uploader">
            <span class="upload-icon">☁️</span>
            <p style='margin-top: 10px; font-weight: 700;'>Drag and drop file here</p>
            <p>Limit 200MB per file - XLSX, CSV</p>
        </div>
        """, unsafe_allow_html=True)
    # Se simula el archivo adjunto "prueba_1.xlsx"
    st.markdown("""
        <div class="attached-file">
            <span class="file-icon">📄</span>
            <span style='margin-left: 10px; font-weight: 700;'>prueba_1.xlsx</span>
            <span style='margin-left: 5px;'>7.5MB</span>
        </div>
        """, unsafe_allow_html=True)

# 5. MENSAJE DE REGISTROS CARGADOS (Azul)
st.markdown("""
    <div class="info-box">
        <span class="clipboard-icon">📋</span>
        <span>Se han cargado 17805 registros correctamente.</span>
    </div>
    """, unsafe_allow_html=True)

# 6. BOTÓN PROCESAR (Azul Oscuro)
st.markdown("""
    <button class="procesar-btn">
        🚀 PROCESAR
    </button>
    """, unsafe_allow_html=True)

# 7. LÍNEA HORIZONTAL PROMINENTE
st.markdown("<hr class='divider-prominent'>", unsafe_allow_html=True)

# 8. MENSAJE DE ÉXITO (Verde)
st.markdown("""
    <div class="success-box">
        <span class="check-icon">✅</span>
        <span>¡Proceso completado con éxito!</span>
    </div>
    """, unsafe_allow_html=True)

# 9. TABLA DE DATOS DE RESULTADOS
# Recreación de los datos exactos que se ven en la imagen de referencia.
data = {
    "GES_estado_cliente": ["T", "T", "T", "T", "T"],
    "FDL_identificador_documento": [7854512, 8002948, 8003029, 7854272, 7854273],
    "FDL_referencia_documento": ["0:00:06", "0:11:39", "0:00:38", "0:00:29", "0:00:15"],
    "FDL_username_originador": [
        "BRAULIO IGNACIO ARENAS SOTO",
        "CLAUDIA CORDOVA",
        "CARMEN GLORIA FAVIO YANEZ",
        "ALEJANDRA MARIN AZOCAR",
        "ALEJANDRA MARIN AZOCAR"
    ],
    "GES_descripcion_1": ["", "", "", "", ""],
    "GES_descripcion_2": ["", "", "", "", ""],
    "GES_descripcion_3": ["", "", "", "", ""],
    "GES_nombre_campana_gestion": ["", "SU", "BCIHOGAR", "", ""], # Coincide con los datos visibles
    "GES_dato_variable_05": ["", "", "", "", ""],
    "GES_dato_variable_26": ["", "", "", "", ""],
    "GES_dato_variable_27": ["032026", "032026", "032026", "032026", "032026"]
}
df = pd.DataFrame(data)

# Orden exacto de las columnas visible en la imagen de referencia.
cols = [
    "GES_estado_cliente", "FDL_identificador_documento", "FDL_referencia_documento",
    "FDL_username_originador", "GES_descripcion_1", "GES_descripcion_2",
    "GES_descripcion_3", "GES_nombre_campana_gestion", "GES_dato_variable_05",
    "GES_dato_variable_26", "GES_dato_variable_27"
]
df = df[cols]

# Se muestra la tabla de datos
st.dataframe(df, use_container_width=True)
