"""
app.py — Interfaz de usuario para el generador de horarios.
Solo contiene código de Streamlit; la lógica vive en utils.py.

Si te paseas por acá recuerda: no soy un experto ni un amateur,
solo alguien curioso que tenía una laptop, YouTube y ayuda de IA.
"""

import streamlit as st
from utils import (
    cargar_materias,
    buscar_por_nombre,
    filtrar_por_nrcs,
    parsear_nrcs,
    agregar_columnas_temporales,
    detectar_empalmes,
    construir_figura,
)

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Mi Horario",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("⚙️ Krea-t tu horario")
st.markdown("Consulta el catálogo de materias y genera tu horario para este periodo.")

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    return cargar_materias("materias.csv")


try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo materias.csv en el directorio principal.")
    st.stop()

# ---------------------------------------------------------------------------
# Layout: dos columnas
# ---------------------------------------------------------------------------

col1, col2 = st.columns([1, 2])

# — Columna izquierda: buscador del catálogo —
with col1:
    st.subheader("🔍 Catálogo")
    busqueda = st.text_input("Buscar materia por nombre:")

    if busqueda:
        resultados = buscar_por_nombre(df, busqueda)
        if resultados.empty:
            st.info("No se encontraron resultados.")
        else:
            columnas_visibles = ["NRC", "Materia", "Dias", "Horario", "Profesor"]
            st.dataframe(
                resultados[columnas_visibles],
                hide_index=True,
                use_container_width=True,
            )

# — Columna derecha: generador de horario —
with col2:
    st.subheader("🗓️ Horario Interperiodo Verano")
    nrc_texto = st.text_input(
        "📚 Ingresa tus NRCs (separados por comas):", "40568"
    )
    mis_nrcs = parsear_nrcs(nrc_texto)

    if mis_nrcs:
        mi_horario = filtrar_por_nrcs(df, mis_nrcs)

        if mi_horario.empty:
            st.warning("No se encontraron materias con esos NRC.")
        else:
            mi_horario = agregar_columnas_temporales(mi_horario)
            empalmes = detectar_empalmes(mi_horario)

            if empalmes:
                st.error("🚨 **¡EMPALME DETECTADO!**")
                for mensaje in empalmes:
                    st.write("- " + mensaje)
                st.info("Por favor, corrige los NRC para poder graficar el plano.")
            else:
                st.success("✅ No se detectaron empalmes.")
                fig = construir_figura(mi_horario)
                st.plotly_chart(fig, use_container_width=True, theme=None)

# ---------------------------------------------------------------------------
# Pie de página
# ---------------------------------------------------------------------------

st.markdown("Recuerda tomar captura de tu horario.")
st.markdown(
    "Si alguien me pregunta por ti, diré que estoy todos los días "
    "alejando mi yo de ti — Marcos Algonia"
)
