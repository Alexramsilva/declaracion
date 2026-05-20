# app.py

import streamlit as st
import pdfplumber
import pandas as pd
import json

from openai import OpenAI

# -----------------------------------
# CONFIG STREAMLIT
# -----------------------------------

st.set_page_config(
    page_title="Asistente Fiscal SAT",
    layout="wide"
)

st.title("📄 Asistente Fiscal SAT")

st.write(
    "Sube constancias fiscales de CETES Directo o GBM"
)

# -----------------------------------
# API KEY INPUT
# -----------------------------------

api_key = st.text_input(
    "Ingresa tu OpenAI API Key",
    type="password"
)

# -----------------------------------
# VALIDAR API KEY
# -----------------------------------

if api_key:

    client = OpenAI(
        api_key=api_key
    )

    st.success("API Key cargada correctamente")

    # -----------------------------------
    # SUBIR PDF
    # -----------------------------------

    uploaded_file = st.file_uploader(
        "Sube tu constancia PDF",
        type=["pdf"]
    )

    # -----------------------------------
    # EXTRAER TEXTO PDF
    # -----------------------------------

    def extraer_texto_pdf(pdf_file):

        texto = ""

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                contenido = page.extract_text()

                if contenido:
                    texto += contenido + "\n"

        return texto

    # -----------------------------------
    # ANALIZAR CONSTANCIA
    # -----------------------------------

    def analizar_constancia(texto):

        prompt = f"""
        Analiza la siguiente constancia fiscal mexicana.

        Extrae:

        - interés nominal
        - interés real
        - ISR retenido
        - resultado fiscal FIBRAS
        - reembolso de capital
        - dividendos
        - pérdidas

        Clasifica como:
        - acumulable
        - acreditable
        - no acumulable

        Devuelve SOLO JSON válido.

        Formato:

        {{
            "conceptos":[
                {{
                    "concepto":"Interés Real",
                    "monto":4226.54,
                    "tratamiento":"acumulable"
                }}
            ],
            "resumen": {{
                "ingreso_acumulable": 0,
                "isr_acreditable": 0,
                "no_acumulable": 0
            }}
        }}

        CONSTANCIA:

        {texto}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto fiscal mexicano "
                        "especializado en SAT, CETES, GBM y FIBRAS."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content

    # -----------------------------------
    # PROCESAR PDF
    # -----------------------------------

    if uploaded_file is not None:

        st.success("PDF cargado correctamente")

        with st.spinner("Extrayendo texto del PDF..."):

            texto_pdf = extraer_texto_pdf(uploaded_file)

        st.subheader("📑 Texto Detectado")

        st.text_area(
            "Contenido PDF",
            texto_pdf,
            height=250
        )

        # -----------------------------------
        # ANALIZAR
        # -----------------------------------

        if st.button("Analizar Constancia"):

            with st.spinner("Analizando información fiscal..."):

                resultado = analizar_constancia(texto_pdf)

            st.subheader("📊 Resultado Fiscal")

            try:

                datos = json.loads(resultado)

                conceptos = datos["conceptos"]

                df = pd.DataFrame(conceptos)

                st.dataframe(
                    df,
                    use_container_width=True
                )

                resumen = datos["resumen"]

                st.subheader("🧾 Resumen SAT")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Ingreso Acumulable",
                    f"${resumen['ingreso_acumulable']:,.2f}"
                )

                col2.metric(
                    "ISR Acreditable",
                    f"${resumen['isr_acreditable']:,.2f}"
                )

                col3.metric(
                    "No Acumulable",
                    f"${resumen['no_acumulable']:,.2f}"
                )

                # -----------------------------------
                # DESCARGAR CSV
                # -----------------------------------

                csv = df.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="⬇ Descargar CSV",
                    data=csv,
                    file_name="resultado_fiscal.csv",
                    mime="text/csv"
                )

            except Exception as e:

                st.error("Error procesando JSON")

                st.write(resultado)

                st.write(e)

else:

    st.info("Ingresa tu OpenAI API Key para comenzar")
