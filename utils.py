import pandas as pd
import itertools

def hms_a_decimal(hms_str):
    h, m, s = map(int, hms_str.split(':'))
    return h + (m / 60.0) + (s / 3600.0)

def calcular_horas_muertas(df_horario):
    horas_muertas_totales = 0
    for dia, clases_del_dia in df_horario.groupby('Dias'):
        clases = clases_del_dia.sort_values('start_dec').reset_index(drop=True)
        for i in range(len(clases) - 1):
            fin_clase_actual = clases.loc[i, 'end_dec']
            inicio_siguiente = clases.loc[i+1, 'start_dec']
            tiempo_libre = inicio_siguiente - fin_clase_actual
            if tiempo_libre > 0:
                horas_muertas_totales += tiempo_libre
    return horas_muertas_totales

def generar_horarios_optimos(df_completo, lista_nombres_materias, max_horas_muertas=4):
    opciones_por_materia = []
    
    for nombre in lista_nombres_materias:
        nrcs_disponibles = df_completo[df_completo['Materia'].str.contains(nombre, case=False, na=False)]['NRC'].unique()
        if len(nrcs_disponibles) == 0:
            return None, f"No se encontró ningún grupo para la materia: {nombre}"
        opciones_por_materia.append(nrcs_disponibles)
        
    todas_combinaciones = list(itertools.product(*opciones_por_materia))
    horarios_validos = []
    
    for combo_nrcs in todas_combinaciones:
        df_combo = df_completo[df_completo['NRC'].isin(combo_nrcs)].copy()
        df_combo['start_dec'] = df_combo['Hora_ini'].apply(hms_a_decimal)
        df_combo['end_dec'] = df_combo['Hora_fin'].apply(hms_a_decimal)
        
        hay_empalme = False
        for dia, clases_del_dia in df_combo.groupby('Dias'):
            clases = clases_del_dia.sort_values('start_dec').reset_index(drop=True)
            for i in range(len(clases) - 1):
                if clases.loc[i+1, 'start_dec'] < clases.loc[i, 'end_dec']:
                    hay_empalme = True
                    break
            if hay_empalme:
                break
                
        if not hay_empalme:
            h_muertas = calcular_horas_muertas(df_combo)
            if h_muertas <= max_horas_muertas:
                horarios_validos.append({
                    'nrcs': combo_nrcs,
                    'horas_muertas': round(h_muertas, 2),
                    'df': df_combo
                })
                
    horarios_validos.sort(key=lambda x: x['horas_muertas'])
    return horarios_validos, "Éxito"