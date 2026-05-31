#"""
#app.py — Interfaz de usuario para el generador de horarios.
#Solo contiene código de Streamlit; la lógica vive en utils.py.

#Si te paseas por acá recuerda: no soy un experto ni un amateur,
#solo alguien curioso que tenía una laptop, YouTube y ayuda de IA.
#"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import generar_horarios_optimos, hms_a_decimal 

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------


st.set_page_config(page_title="Mi Horario", layout="wide", initial_sidebar_state="collapsed")
st.title("⚙️ Krea-t tu horario")

@st.cache_data
def load_data():
    return pd.read_csv('materias.csv')

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo materias.csv")
    st.stop()

# --- PESTAÑAS ---
tab_manual, tab_algoritmo = st.tabs(["Cuentas con tus NRCs", "🤖 Generador Automático"])

with tab_manual:
    st.markdown("Consulta el catálogo de materias y genera tu horario para este periodo.")
    
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

    if modo == "Mis NRC":    nrc_texto = st.text_input(
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

    
    
with tab_algoritmo:
    st.markdown("Selecciona las materias y deja que el algoritmo encuentre las mejores combinaciones sin empalmes.")
    
    todas_las_materias = sorted(df['Materia'].unique())
    materias_deseadas = st.multiselect("Elige tus materias:", todas_las_materias)
    limite_horas = st.slider("Máximo de horas muertas toleradas por semana:", 0, 10, 4)

    if st.button("Generar Horarios"):
        if len(materias_deseadas) > 0:
            with st.spinner('Procesando combinaciones...'):
                horarios_generados, mensaje = generar_horarios_optimos(df, materias_deseadas, limite_horas)
                
                if horarios_generados is None:
                    st.error(mensaje)
                elif len(horarios_generados) == 0:
                    st.warning("No se encontró ningún horario viable con esas restricciones.")
                else:
                    st.success(f"¡Se encontraron {len(horarios_generados)} horarios viables!")
                    
                    mejor_horario = horarios_generados[0]
                    st.markdown(f"### 🏆 Opción Óptima")
                    st.write(f"**NRCs a inscribir:** {', '.join(map(str, mejor_horario['nrcs']))}")
                    st.write(f"**Horas libres a la semana:** {mejor_horario['horas_muertas']} hrs")
                    
        else:
            st.info("Por favor selecciona al menos una materia para comenzar.")
st.markdown("Recuerda tomar captura de tu horario.")
st.markdown(
    "Aún no tomo en cuenta los créditos, entonces eso debería de quedar a tu consideración :p "
    

st.markdown(
    "Si alguien me pregunta por ti, diré que estoy todos los días "
    "alejando mi yo de ti — Marcos Algonia")
