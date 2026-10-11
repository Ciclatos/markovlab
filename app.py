import hashlib
import textwrap
import altair as alt
import streamlit as st
from groq import Groq

from main import (
    extraer_texto_pdf,
    clasificar_texto,
    contar_transiciones,
    calcular_matriz,
    calcular_pasos,
    calcular_estacionaria,
)

st.set_page_config(page_title="MarkovLab", page_icon="📊", layout="wide")

# Guardar la interpretación de la IA
if "interpretacion" not in st.session_state:
    st.session_state.interpretacion = None
if "documento_analizado" not in st.session_state:
    st.session_state.documento_analizado = None

# Encabezado principal
st.markdown(textwrap.dedent("""
<div style="padding: 32px; border-radius: 16px; background: linear-gradient(120deg, #142744, #101827); border: 1px solid #294365; margin-bottom: 28px;">
    <p style="color: #93C5FD; font-size: 12px; letter-spacing: 2px; font-weight: 600; margin-bottom: 10px;">LABORATORIO DE ANÁLISIS ESTADÍSTICO</p>
    <h1 style="color: #FFFFFF; font-size: 42px; margin: 0;">MarkovLab</h1>
    <p style="color: #CBD5E1; font-size: 16px; margin-top: 12px; margin-bottom: 0;">Análisis de documentos mediante cadenas de Markov e inteligencia artificial.</p>
</div>
"""), unsafe_allow_html=True)

# Subir el documento
archivo = st.file_uploader("Selecciona un documento PDF", type=["pdf"])

if archivo is not None:
    # Reiniciar la interpretación al cambiar de PDF
    identificador = hashlib.sha256(archivo.getvalue()).hexdigest()
    if st.session_state.documento_analizado != identificador:
        st.session_state.interpretacion = None
        st.session_state.documento_analizado = identificador

    # Calcular los resultados antes de mostrar las pestañas
    texto = extraer_texto_pdf(archivo.getvalue())
    secuencia = clasificar_texto(texto)
    frecuencias = contar_transiciones(secuencia)

    tab_documento, tab_estadistica, tab_ia = st.tabs(
        ["📄 Documento", "📊 Análisis estadístico", "✨ Inteligencia artificial"]
    )

    with tab_documento:
        st.success("PDF cargado correctamente")
        st.write("Archivo:", archivo.name)
        st.subheader("Texto extraído")
        st.text_area("Contenido del documento", texto, height=250)
        st.write("Caracteres extraídos:", len(texto))
        st.write("Letras analizadas:", len(secuencia))

    # Comprobar que haya suficientes datos
    if len(secuencia) < 2:
        with tab_documento:
            st.error("El documento no contiene suficientes letras para analizar.")
        st.stop()

    total_v = frecuencias["VV"] + frecuencias["VC"]
    total_c = frecuencias["CV"] + frecuencias["CC"]
    if total_v == 0 or total_c == 0:
        with tab_documento:
            st.warning("Se necesitan transiciones desde vocales y consonantes.")
        st.stop()

    matriz = calcular_matriz(frecuencias)
    estacionaria = calcular_estacionaria(matriz)

    with tab_estadistica:
        st.subheader("Análisis de transiciones")
        st.write("Letras analizadas:", len(secuencia))
        st.write("Total de transiciones:", sum(frecuencias.values()))

        # Mostrar las frecuencias
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("VV", frecuencias["VV"])
        col2.metric("VC", frecuencias["VC"])
        col3.metric("CV", frecuencias["CV"])
        col4.metric("CC", frecuencias["CC"])

        # Gráfico de las transiciones
        st.subheader("Gráfico de transiciones")
        datos = [
            {"Transición": tipo, "Frecuencia": cantidad}
            for tipo, cantidad in frecuencias.items()
        ]
        grafico = alt.Chart(alt.Data(values=datos)).mark_bar(
            cornerRadiusEnd=5
        ).encode(
            x=alt.X(
                "Frecuencia:Q",
                title="Cantidad de transiciones",
                scale=alt.Scale(domainMin=0),
            ),
            y=alt.Y(
                "Transición:N",
                title=None,
                sort=["VV", "VC", "CV", "CC"],
            ),
            tooltip=["Transición:N", "Frecuencia:Q"],
        ).properties(height=220)
        st.altair_chart(grafico, use_container_width=True)

        # Frecuencias relativas
        total = sum(frecuencias.values())
        st.subheader("Frecuencias relativas")
        for transicion, cantidad in frecuencias.items():
            porcentaje = cantidad / total * 100
            st.write(f"{transicion}: {porcentaje:.2f}%")

        # Matriz de transición
        st.subheader("Matriz de transición")
        st.dataframe(
            {
                "Estado": ["V", "C"],
                "V": [matriz[0][0], matriz[1][0]],
                "C": [matriz[0][1], matriz[1][1]],
            },
            hide_index=True,
        )

        # Mapa de calor de la matriz
        st.subheader("Mapa de calor")
        datos_matriz = [
            {"Origen": "V", "Destino": "V", "Probabilidad": matriz[0][0]},
            {"Origen": "V", "Destino": "C", "Probabilidad": matriz[0][1]},
            {"Origen": "C", "Destino": "V", "Probabilidad": matriz[1][0]},
            {"Origen": "C", "Destino": "C", "Probabilidad": matriz[1][1]},
        ]
        mapa_calor = alt.Chart(
            alt.Data(values=datos_matriz)
        ).mark_rect().encode(
            x=alt.X("Destino:N", title="Estado siguiente", sort=["V", "C"]),
            y=alt.Y("Origen:N", title="Estado actual", sort=["V", "C"]),
            color=alt.Color(
                "Probabilidad:Q",
                scale=alt.Scale(domain=[0, 1]),
                title="Probabilidad",
            ),
            tooltip=[
                "Origen:N",
                "Destino:N",
                alt.Tooltip("Probabilidad:Q", format=".2%"),
            ],
        ).properties(height=250)
        etiquetas = alt.Chart(
           alt.Data(values=datos_matriz)
       ).mark_text(fontSize=18, fontWeight="bold").encode(
           x=alt.X("Destino:N", sort=["V", "C"]),
           y=alt.Y("Origen:N", sort=["V", "C"]),
           text=alt.Text("Probabilidad:Q", format=".1%"),
           color=alt.condition(
               alt.datum.Probabilidad >= 0.5,
               alt.value("#172033"),
               alt.value("#FFFFFF"),
           ),
       )
        st.altair_chart(mapa_calor + etiquetas, use_container_width=True)

        # Verificar la matriz
        st.subheader("Verificación de la matriz")
        filas_validas = True
        for i, fila in enumerate(matriz):
            suma = sum(fila)
            estado = "V" if i == 0 else "C"
            if abs(suma - 1) < 0.000001:
                st.write(f"Fila {estado}: {suma:.4f} ✓")
            else:
                filas_validas = False
                st.error(f"Fila {estado}: la suma no es 1")
        probabilidades_validas = all(
            0 <= valor <= 1 for fila in matriz for valor in fila
        )
        if filas_validas and probabilidades_validas:
            st.success("La matriz cumple las propiedades estocásticas.")
        else:
            st.error("La matriz no cumple las propiedades estocásticas.")

        # Probabilidades a n pasos
        st.subheader("Probabilidades a n pasos")
        n = st.slider("Número de pasos", min_value=1, max_value=20, value=5)
        resultado = calcular_pasos(matriz, n)
        st.write(f"Matriz P^{n}")
        st.dataframe(
            {
                "Estado": ["V", "C"],
                "V": [resultado[0][0], resultado[1][0]],
                "C": [resultado[0][1], resultado[1][1]],
            },
            hide_index=True,
        )

        # Distribución estacionaria
        st.subheader("Distribución estacionaria")
        col1, col2 = st.columns(2)
        col1.metric("Vocales (V)", f"{estacionaria[0] * 100:.2f}%")
        col2.metric("Consonantes (C)", f"{estacionaria[1] * 100:.2f}%")
        datos_estacionaria = [
            {"Estado": "Vocales", "Probabilidad": estacionaria[0]},
            {"Estado": "Consonantes", "Probabilidad": estacionaria[1]},
        ]
        grafico_estacionaria = alt.Chart(
            alt.Data(values=datos_estacionaria)
        ).mark_arc(innerRadius=65).encode(
            theta=alt.Theta("Probabilidad:Q"),
            color=alt.Color("Estado:N", legend=alt.Legend(title="Estado")),
            tooltip=[
                "Estado:N",
                alt.Tooltip("Probabilidad:Q", format=".2%"),
            ],
        ).properties(height=280)
        st.altair_chart(grafico_estacionaria, use_container_width=True)
        # Explicar la distribución estacionaria
        st.info(
        "La distribución estacionaria es una distribución de probabilidades "
        "que permanece igual después de aplicar la matriz de transición. "
        "No todas las cadenas convergen a ella desde cualquier estado inicial."
        )

    with tab_ia:
        # Interpretar los resultados con IA
        st.subheader("Interpretación con inteligencia artificial")
        if st.button("Analizar resultados con IA"):
            prompt = f"""
            Eres un profesor universitario de estadística.

            Analiza los siguientes resultados de una cadena de Markov
            de dos estados: Vocal (V) y Consonante (C).

            Frecuencias absolutas: {frecuencias}
            Matriz de transición: {matriz}
            Distribución estacionaria: {estacionaria}

            Explica brevemente:
            1. Qué indican las frecuencias de transición.
            2. Cómo interpretar la matriz.
            3. Qué significa la distribución estacionaria.

            Utiliza lenguaje claro, preciso y en español.
            No inventes datos ni realices cálculos nuevos.
            
            Presenta la respuesta con títulos y párrafos breves.
            Puedes utilizar listas cuando ayuden a explicar los resultados.
            No utilices LaTeX ni escribas fórmulas matemáticas.
            No generes tablas, porque la aplicación ya muestra
            las matrices y los gráficos correspondientes.
            Explica las probabilidades utilizando porcentajes.
            Evita repetir innecesariamente todos los números.
            """
            with st.spinner("IA está analizando los resultados..."):
                try:
                    cliente = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    respuesta = cliente.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                    )
                    st.session_state.interpretacion = (
                        respuesta.choices[0].message.content
                    )
                except Exception as error:
                    st.error(f"No se pudo completar el análisis: {error}")

        # Mostrar la interpretación guardada
        if st.session_state.interpretacion is not None:
            st.markdown(st.session_state.interpretacion)
