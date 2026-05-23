# app.py

import streamlit as st
import pdfplumber
import pandas as pd
import json

from openai import OpenAI

# ---------------------------------------------------
# CONFIG STREAMLIT
# ---------------------------------------------------
st.image("UNRC.png", caption="Universidad Nacional Rosario Castellanos", width=300)

st.set_page_config(
    page_title="Plataforma RegTech basada en IA para automatizar la interpretación fiscal y patrimonial de inversiones bursátiles mexicanas orientadas al cumplimiento DECLARANET y SAT.",
    layout="wide"
)

st.title("Asistente DECLARANET para inversionista GBM del Sector Público Federal")

st.write(
    "Sube tus constancias de información fiscal de GBM"
)

# ---------------------------------------------------
# API KEY
# ---------------------------------------------------

api_key = st.text_input(
    "Ingresa tu OpenAI API Key",
    type="password"
)

# ---------------------------------------------------
# VALIDAR API
# ---------------------------------------------------

if api_key:

    client = OpenAI(
        api_key=api_key
    )

    st.success("API Key cargada correctamente, sigue adelante.")

    # ---------------------------------------------------
    # SUBIR PDF
    # ---------------------------------------------------

    uploaded_file = st.file_uploader(
        "Sube tu constancia de información fiscal PDF",
        type=["pdf"]
    )

    # ---------------------------------------------------
    # EXTRAER TEXTO PDF
    # ---------------------------------------------------

    def extraer_texto_pdf(pdf_file):

        texto = ""

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                contenido = page.extract_text()

                if contenido:
                    texto += contenido + "\n"

        return texto

    # ---------------------------------------------------
    # ANALIZAR CONSTANCIA
    # ---------------------------------------------------

    def analizar_constancia(texto):

        prompt = f"""
        Analiza la siguiente constancia fiscal mexicana emitida por GBM o casa de bolsa.

        Extrae EXACTAMENTE los siguientes conceptos:

        1. ACCIONES
        - Ganancias
        - Pérdidas
        - Resultado Neto

        2. INTERESES
        - Interés Nominal Gravado
        - Interés Nominal Exento
        - Total de Interés Nominal
        - Interés Real Gravado
        - Pérdida Real por Intereses
        - ISR Retenido Acreditable

        3. FIBRAS
        - Resultado Fiscal Distribuido por Fibras
        - ISR Retenido Acreditable por Fibras
        - Ganancia Inmuebles Fideicomitidos
        - ISR Pagado por la Fiduciaria (FIBRAS)
        - Reembolso de Capital

        4. DIVIDENDOS NACIONALES
        - Dividendos Pagados
        - Dividendos Acumulables
        - ISR Acreditable por Dividendos

        5. DIVIDENDOS EXTRANJEROS
        - Dividendos Pagados Extranjeras (SIC)
        - Impuesto Retenido en el Extranjero

        INVERSIONES
        - Interés Nominal
        - Interés Real
        - Impuesto Sobre la Renta Retenido

        INVERSIONES BONDDIA
        - Interés Nominal
        - Interés Real
        - Impuesto Sobre la Renta Retenido

        Clasifica cada concepto, despues de impuestos, para DECLARANET
        utilizando SOLAMENTE una de las siguientes categorías:

        - Capital
        - Valores Bursátiles
        - Bonos

        Reglas importantes:

        - Resultado Neto de acciones -> Valores Bursátiles
        - (Interés Real Gravado-Pérdida Real por Intereses-ISR Retenido Acreditable) -> Bonos
        - (Interés Real-Impuesto Sobre la Renta Retenido) -> Bonos        
        - (Resultado Fiscal Distribuido por Fibras-ISR Retenido Acreditable por Fibras) -> Valores Bursátiles
        - Dividendos Pagados -> Capital
        - Dividendos Pagados Extranjeras (SIC) -> Capital
        - Reembolso de Capital -> Capital
        - ISR acreditable debe conservarse como acreditable
        - Si un concepto no existe, usar 0
        - Todos los montos deben ser numéricos
        - No agregar texto fuera del JSON

        Devuelve SOLO JSON válido.

        Formato EXACTO:

        {{
            "conceptos":[
                {{
                    "categoria":"Valores Bursátiles",
                    "concepto":"Resultado Neto",
                    "monto":840.12,
                    "tipo":"acumulable"
                }},
                {{
                    "categoria":"Bonos",
                    "concepto":"ISR Retenido Acreditable",
                    "monto":2.21,
                    "tipo":"acreditable"
                }}
            ],

            "resumen": {{
                "Capital": 0,
                "Valores Bursátiles": 0,
                "Bonos": 0
            }}
        }}

        La sección "resumen" debe sumar únicamente montos acumulables
        por categoría.

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
                        "especializado en SAT, GBM, CETES y DECLARANET, egresado de la UNRC."
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

    # ---------------------------------------------------
    # PROCESAR PDF
    # ---------------------------------------------------

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

        # ---------------------------------------------------
        # BOTÓN ANALIZAR
        # ---------------------------------------------------

        if st.button("Analizar Constancia"):

            with st.spinner("Analizando información fiscal..."):

                resultado = analizar_constancia(texto_pdf)

            st.subheader("Resultado Fiscal")

            try:

                datos = json.loads(resultado)

                conceptos = datos["conceptos"]

                df = pd.DataFrame(conceptos)

                st.dataframe(
                    df,
                    use_container_width=True
                )

                resumen = datos["resumen"]

                st.subheader("🧾 Resumen DECLARANET")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Capital",
                    f"${resumen['Capital']:,.2f}"
                )

                col2.metric(
                    "Valores Bursátiles",
                    f"${resumen['Valores Bursátiles']:,.2f}"
                )

                col3.metric(
                    "Bonos",
                    f"${resumen['Bonos']:,.2f}"
                )

                # ---------------------------------------------------
                # DESCARGAR CSV
                # ---------------------------------------------------

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

                st.error("Error procesando respuesta JSON")

                st.write(resultado)

                st.write(e)

else:

    st.info("Ingresa tu OpenAI API Key para comenzar")
