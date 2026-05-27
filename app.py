import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Mi Horario", layout="wide", initial_sidebar_state="collapsed")
st.title("⚙️ Sistema Automatizado de Horarios")
st.markdown("Consulta el catálogo de materias y genera tu plano maestro de clases.")

@st.cache_data
def load_data():
    # RUTA ACTUALIZADA PARA GITHUB: Asume que el CSV está en la misma carpeta que este código
    return pd.read_csv('materias.csv')

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo materias.csv en el directorio principal.")
    st.stop()

col1, col2 = st.columns([1, 2])

# ==========================================
# COLUMNA 1: CATÁLOGO DE MATERIAS
# ==========================================
with col1:
    st.subheader("🔍 Catálogo")
    busqueda = st.text_input("Buscar materia por nombre:")
    
    if busqueda:
        resultados = df[df['Materia'].str.contains(busqueda, case=False, na=False)].copy()
        if resultados.empty:
            st.info("No se encontraron resultados.")
        else:
            resultados['Horario'] = resultados['Hora_ini'].astype(str) + " - " + resultados['Hora_fin'].astype(str)
            st.dataframe(resultados[['NRC', 'Materia', 'Dias', 'Horario', 'Profesor']], hide_index=True, use_container_width=True)

# ==========================================
# COLUMNA 2: GENERADOR DE PLANO Y EMPALMES
# ==========================================
with col2:
    st.subheader("🗓️ Plano Maestro")
    nrc_texto = st.text_input("📚 Ingresa tus NRCs (separados por comas):", "40996, 40568, 40497")
    mis_nrcs = [int(nrc.strip()) for nrc in nrc_texto.split(",") if nrc.strip().isdigit()]

    if len(mis_nrcs) > 0:
        mi_horario = df[df['NRC'].isin(mis_nrcs)].copy()
        
        if mi_horario.empty:
            st.warning("No se encontraron materias con esos NRC.")
        else:
            map_dias_num = {'L': 1, 'A': 2, 'M': 3, 'J': 4, 'V': 5}
            mi_horario['Dia_Num'] = mi_horario['Dias'].map(map_dias_num)

            def hms_a_decimal(hms_str):
                h, m, s = map(int, hms_str.split(':'))
                return h + (m / 60.0) + (s / 3600.0)

            mi_horario['Hora_ini'] = mi_horario['Hora_ini'].astype(str)
            mi_horario['Hora_fin'] = mi_horario['Hora_fin'].astype(str)
            mi_horario['start_dec'] = mi_horario['Hora_ini'].apply(hms_a_decimal)
            mi_horario['end_dec'] = mi_horario['Hora_fin'].apply(hms_a_decimal)
            mi_horario['duration_dec'] = mi_horario['end_dec'] - mi_horario['start_dec']

            # --- DETECTOR LÓGICO DE EMPALMES ---
            empalmes = []
            for dia, clases_del_dia in mi_horario.groupby('Dias'):
                clases = clases_del_dia.sort_values('start_dec').reset_index(drop=True)
                for i in range(len(clases) - 1):
                    if clases.loc[i+1, 'start_dec'] < clases.loc[i, 'end_dec']:
                        empalmes.append(f"El día {dia}, **{clases.loc[i, 'Materia']}** choca con **{clases.loc[i+1, 'Materia']}**.")
            
            if empalmes:
                st.error("🚨 **¡ALERTA DE EMPALME DETECTADA!**")
                for e in empalmes:
                    st.write("- " + e)
                st.info("Por favor, corrige los NRC para poder graficar el plano.")
            else:
                st.success("✅ Estructura viable. No se detectaron empalmes.")
                
                # --- RENDERIZADO DEL GRÁFICO (Si no hay empalmes) ---
                fig = go.Figure()
                colors = px.colors.qualitative.Plotly
                materia_to_color = {materia: colors[i % len(colors)] for i, materia in enumerate(mi_horario['Materia'].unique())}
                mi_horario['Color'] = mi_horario['Materia'].map(materia_to_color)

                for materia, group in mi_horario.groupby('Materia'):
                    custom_data = group[['Profesor', 'Salón', 'Hora_ini', 'Hora_fin']].values
                    fig.add_trace(go.Bar(
                        name=materia, x=group['Dia_Num'], y=group['duration_dec'], base=group['start_dec'],
                        marker_color=group['Color'].iloc[0], customdata=custom_data, text=group['Materia'],
                        textposition='inside', insidetextanchor='middle',
                        hovertemplate="<b>%{text}</b><br><br><b>Profesor:</b> %{customdata[0]}<br><b>Salón:</b> %{customdata[1]}<br><b>Horario:</b> %{customdata[2]} - %{customdata[3]}<br><extra></extra>"
                    ))

                horas_numeros = list(range(7, 22)) 
                horas_texto = [f"{h:02d}:00" for h in horas_numeros]

                fig.update_layout(
                    barmode='overlay', paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black'), height=700,
                    xaxis=dict(title="", side='top', tickmode='array', tickvals=[1, 2, 3, 4, 5], ticktext=['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'], showgrid=True, gridcolor='#d3d3d3', zeroline=False),
                    yaxis=dict(title="Horario", range=[21.5, 6.5], tickmode='array', tickvals=horas_numeros, ticktext=horas_texto, showgrid=True, gridcolor='#d3d3d3', zeroline=False),
                    margin=dict(l=40, r=40, t=60, b=40)
                )

                st.plotly_chart(fig, use_container_width=True, theme=None)
