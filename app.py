import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Resultantes BCI - Recaall", page_icon="🏦")

st.title("🏦 Procesador de Resultantes BCI")
st.write("Herramienta interna para la transformación de datos.")

# Subida de archivo
uploaded_file = st.file_uploader("Sube el archivo Excel original aquí", type=["xlsx"])

if uploaded_file:
    # Leer el excel
    df = pd.read_excel(uploaded_file)
    
    st.success("Archivo cargado con éxito.")
    st.write("### Vista previa de los datos:")
    st.dataframe(df.head())

    # Aquí irá la lógica de transformación que definamos después
    df_transformado = df.copy() 

    # Botón para descargar el resultado
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_transformado.to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Descargar Formato BCI",
        data=output.getvalue(),
        file_name="resultante_bci_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
