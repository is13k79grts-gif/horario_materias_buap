"""
utils.py — Lógica de negocio para la app de horarios.
Separado de la UI para facilitar pruebas y reutilización.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def cargar_materias(ruta: str = "materias.csv") -> pd.DataFrame:
    """Lee el CSV de materias y lo retorna como DataFrame."""
    return pd.read_csv(ruta)


def buscar_por_nombre(df: pd.DataFrame, texto: str) -> pd.DataFrame:
    """Filtra materias cuyo nombre contenga `texto` (sin importar mayúsculas)."""
    mask = df["Materia"].str.contains(texto, case=False, na=False)
    resultados = df[mask].copy()
    resultados["Horario"] = (
        resultados["Hora_ini"].astype(str) + " - " + resultados["Hora_fin"].astype(str)
    )
    return resultados


def filtrar_por_nrcs(df: pd.DataFrame, nrcs: list[int]) -> pd.DataFrame:
    """Retorna las filas del DataFrame cuyos NRC estén en la lista dada."""
    return df[df["NRC"].isin(nrcs)].copy()


def parsear_nrcs(texto: str) -> list[int]:
    """
    Convierte un string de NRCs separados por comas en una lista de enteros.
    Ignora silenciosamente los tokens que no sean dígitos válidos.
    """
    nrcs = []
    for token in texto.split(","):
        token = token.strip()
        if token.isdigit():
            try:
                nrcs.append(int(token))
            except ValueError:
                pass
    return nrcs


# ---------------------------------------------------------------------------
# Conversión de horarios
# ---------------------------------------------------------------------------

def hms_a_decimal(hms_str: str) -> float:
    """
    Convierte un string 'HH:MM:SS' a horas decimales.
    Redondea al entero más cercano si el error de float es menor a 0.05 h,
    para evitar artefactos como 7.9999... en lugar de 8.0.
    """
    h, m, s = map(int, str(hms_str).split(":"))
    decimal = h + (m / 60.0) + (s / 3600.0)
    if abs(decimal - round(decimal)) < 0.05:
        return round(decimal)
    return decimal


def agregar_columnas_temporales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade columnas de apoyo al DataFrame de materias:
      - Dia_Num   : número de día (Lunes=1 … Viernes=5)
      - start_dec : hora de inicio en decimal
      - end_dec   : hora de fin en decimal
      - duration_dec: duración en horas decimales
    """
    map_dias = {"L": 1, "A": 2, "M": 3, "J": 4, "V": 5}
    df = df.copy()
    df["Dia_Num"] = df["Dias"].map(map_dias)
    df["start_dec"] = df["Hora_ini"].astype(str).apply(hms_a_decimal)
    df["end_dec"] = df["Hora_fin"].astype(str).apply(hms_a_decimal)
    df["duration_dec"] = df["end_dec"] - df["start_dec"]
    return df


# ---------------------------------------------------------------------------
# Detección de empalmes
# ---------------------------------------------------------------------------

def detectar_empalmes(df: pd.DataFrame) -> list[str]:
    """
    Revisa si alguna materia se traslapa con otra en el mismo día.
    Retorna una lista de mensajes descriptivos; lista vacía = sin empalmes.
    """
    mensajes = []
    for dia, clases_del_dia in df.groupby("Dias"):
        clases = clases_del_dia.sort_values("start_dec").reset_index(drop=True)
        # Comparamos cada clase con la siguiente usando shift vectorizado
        fin_anterior = clases["end_dec"].shift(1)
        empalme = clases["start_dec"] < fin_anterior
        for idx in clases[empalme].index:
            materia_actual = clases.loc[idx, "Materia"]
            materia_anterior = clases.loc[idx - 1, "Materia"]
            mensajes.append(
                f"El día {dia}, **{materia_anterior}** choca con **{materia_actual}**."
            )
    return mensajes


# ---------------------------------------------------------------------------
# Construcción de la figura
# ---------------------------------------------------------------------------

def construir_figura(df: pd.DataFrame) -> go.Figure:
    """
    Construye y retorna la figura Plotly del horario semanal.
    Recibe un DataFrame que ya incluye las columnas temporales.
    """
    colors = px.colors.qualitative.Plotly
    materia_to_color = {
        materia: colors[i % len(colors)]
        for i, materia in enumerate(df["Materia"].unique())
    }
    df = df.copy()
    df["Color"] = df["Materia"].map(materia_to_color)

    fig = go.Figure()

    for materia, group in df.groupby("Materia"):
        custom_data = group[["Profesor", "Salón", "Hora_ini", "Hora_fin"]].values
        fig.add_trace(
            go.Bar(
                name=materia,
                x=group["Dia_Num"],
                y=group["duration_dec"],
                base=group["start_dec"],
                marker_color=group["Color"].iloc[0],
                opacity=1.0,
                customdata=custom_data,
                text=group["Materia"],
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate=(
                    "<b>%{text}</b><br><br>"
                    "<b>Profesor:</b> %{customdata[0]}<br>"
                    "<b>Salón:</b> %{customdata[1]}<br>"
                    "<b>Horario:</b> %{customdata[2]} - %{customdata[3]}<br>"
                    "<extra></extra>"
                ),
            )
        )

    horas = list(range(7, 22))

    xaxis_cfg = dict(
        title="",
        side="top",
        tickmode="array",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        showgrid=True,
        gridcolor="#e5e5e5",
        zeroline=False,
    )

    yaxis_cfg = dict(
        title="Horario",
        range=[21.5, 6.5],
        tickmode="array",
        tickvals=horas,
        ticktext=[f"{h:02d}:00" for h in horas],
        showgrid=True,
        gridcolor="#e5e5e5",
        zeroline=False,
    )

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black"),
        height=700,
        xaxis=xaxis_cfg,
        yaxis=yaxis_cfg,
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig
