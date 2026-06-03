import streamlit as st
import numpy as np
import pandas as pd
import re

def sanitizar_dataframe(df):
    """
    Garantiza que el DataFrame contenga las columnas correctas, previniendo
    errores de tipos de datos o divisiones por cero en el plano cartesiano.
    """
    df_clean = df.copy()
    if df_clean.empty:
        return pd.DataFrame(columns=['Factor', 'Peso', 'Calificación'])
        
    if 'Factor' not in df_clean.columns:
        df_clean['Factor'] = 'Nuevo factor'
    if 'Peso' not in df_clean.columns:
        df_clean['Peso'] = 0.25
    if 'Calificación' not in df_clean.columns:
        df_clean['Calificación'] = 3.0

    # Rellenar NaNs y vacíos en Factor de forma segura con autocorrección de texto
    def corregir_texto(val):
        val = str(val or '').strip()
        val = re.sub(r'\s+', ' ', val)
        if not val or val == 'nan':
            return 'Nuevo criterio operacional'
        # Autocorregir capitalizando la primera letra
        return val[0].upper() + val[1:]

    df_clean['Factor'] = df_clean['Factor'].fillna('Nuevo criterio operacional').apply(corregir_texto)

    # Forzar conversión a numéricos de forma segura
    df_clean['Peso'] = pd.to_numeric(df_clean['Peso'], errors='coerce').fillna(0.25)
    df_clean['Calificación'] = pd.to_numeric(df_clean['Calificación'], errors='coerce').fillna(3.0)
    
    # Restringir a los rangos requeridos
    df_clean['Peso'] = np.clip(df_clean['Peso'], 0.0, 1.0)
    df_clean['Calificación'] = np.clip(df_clean['Calificación'], 1.0, 5.0)
    
    return df_clean


def calcular_scores(df_f, df_d, df_o, df_a):
    """Calcula las coordenadas X e Y sobre un plano de -50 a 50."""
    f = sanitizar_dataframe(df_f)
    d = sanitizar_dataframe(df_d)
    o = sanitizar_dataframe(df_o)
    a = sanitizar_dataframe(df_a)
    
    f_total = (f['Peso'] * f['Calificación']).sum() if not f.empty else 0
    d_total = (d['Peso'] * d['Calificación']).sum() if not d.empty else 0
    o_total = (o['Peso'] * o['Calificación']).sum() if not o.empty else 0
    a_total = (a['Peso'] * a['Calificación']).sum() if not a.empty else 0
    
    x = round((f_total - d_total) * 10, 2)
    y = round((o_total - a_total) * 10, 2)
    return x, y

def calcular_mefi_mefe(df_f, df_d, df_o, df_a):
    """Retorna las ponderaciones de cada uno de los cuatro cuadrantes."""
    f = sanitizar_dataframe(df_f)
    d = sanitizar_dataframe(df_d)
    o = sanitizar_dataframe(df_o)
    a = sanitizar_dataframe(df_a)
    
    f_total = (f['Peso'] * f['Calificación']).sum() if not f.empty else 0
    d_total = (d['Peso'] * d['Calificación']).sum() if not d.empty else 0
    o_total = (o['Peso'] * o['Calificación']).sum() if not o.empty else 0
    a_total = (a['Peso'] * a['Calificación']).sum() if not a.empty else 0
    
    return {
        "F": round(f_total, 2), "D": round(d_total, 2),
        "O": round(o_total, 2), "A": round(a_total, 2),
        "interno": round(f_total - d_total, 2), "externo": round(o_total - a_total, 2)
    }

def clasificacion(scores):
    """Determina la clasificación del cuadrante estratégico sin emojis ni corchetes."""
    x, y = scores["interno"], scores["externo"]
    if x > 0 and y > 0: return "ESTADO: DOMINIO TOTAL (OFENSIVA - FO)"
    elif x < 0 and y > 0: return "ESTADO: REORGANIZACIÓN ESTRUCTURAL (DO)"
    elif x > 0 and y < 0: return "ESTADO: RESISTENCIA ESTRATÉGICA (FA)"
    else: return "ESTADO: SUPERVIVENCIA CRÍTICA (DA)"

def alertas(scores):
    """Genera advertencias tácticas en la pantalla sin corchetes."""
    if scores["A"] > scores["O"]:
        st.error("SITUACIÓN DE RIESGO: ENTORNO HOSTIL DETECTADO (A > O)")
    if scores["D"] > scores["F"]:
        st.warning("ADVERTENCIA OPERATIVA: DEBILIDAD INTERNA CRÍTICA (D > F)")
    if scores["F"] > scores["D"] and scores["O"] > scores["A"]:
        st.success("SITUACIÓN ÓPTIMA: SUPERIORIDAD ESTRATÉGICA CONFIRMADA")

def decidir(scores, prob):
    """Propone la directiva estratégica recomendada."""
    x, y = scores["interno"], scores["externo"]
    if prob > 70 and x > 0 and y > 0:
        return "DIRECTIVA ALFA: OFENSIVA TOTAL (Escalar, Expandir y Asignar Recursos)"
    elif prob > 40:
        return "DIRECTIVA BRAVO: ADAPTACIÓN (Reorganizar Líneas, Corregir Vulnerabilidades)"
    elif x > 0:
        return "DIRECTIVA CHARLIE: DEFENSA ACTIVA (Asegurar Fortalezas, Contener Amenazas)"
    else:
        return "DIRECTIVA DELTA: REPLIEGUE Y SUPERVIVENCIA (Reestructuración Crítica)"

def evolucionar(df, tendencia=0.02, volatilidad=0.15):
    """Aplica un movimiento Browniano geométrico simplificado sobre las calificaciones."""
    df2 = sanitizar_dataframe(df)
    if df2.empty:
        return df2
    drift = tendencia * df2['Calificación']
    shock = np.random.normal(0, volatilidad, size=len(df2))
    df2['Calificación'] = np.clip(df2['Calificación'] + drift + shock, 1.0, 5.0)
    return df2

@st.cache_data(max_entries=20, ttl=300)
def simular_periodos(df_f, df_d, df_o, df_a, stress_interno=0.0, stress_externo=0.0, T=12):
    """Simula la trayectoria del vector estratégico a lo largo del tiempo."""
    historia = []
    f = sanitizar_dataframe(df_f)
    d = sanitizar_dataframe(df_d)
    o = sanitizar_dataframe(df_o)
    a = sanitizar_dataframe(df_a)
    
    for t in range(T):
        f = evolucionar(f, tendencia=0.01)
        d = evolucionar(d, tendencia=-0.005)
        o = evolucionar(o, tendencia=0.012)
        a = evolucionar(a, tendencia=0.008)
        x = np.sum(f['Peso'] * f['Calificación']) - np.sum(d['Peso'] * d['Calificación'])
        y = np.sum(o['Peso'] * o['Calificación']) - np.sum(a['Peso'] * a['Calificación'])
        # Aplicar modificadores de estrés
        x_mod = x * 10 - stress_interno
        y_mod = y * 10 - stress_externo
        historia.append((t, x_mod, y_mod))
    return np.array(historia)

@st.cache_data(max_entries=20, ttl=300)
def simulacion_montecarlo(df_f, df_d, df_o, df_a, stress_interno=0.0, stress_externo=0.0, n=1000):
    """Genera n escenarios estocásticos de simulación para determinar riesgo de forma vectorizada y optimizada con caching."""
    f = sanitizar_dataframe(df_f)
    d = sanitizar_dataframe(df_d)
    o = sanitizar_dataframe(df_o)
    a = sanitizar_dataframe(df_a)
    
    # Vectorización completa usando NumPy para máxima velocidad
    if not f.empty:
        f_samples = np.random.normal(f['Calificación'].values, 0.45, size=(n, len(f)))
        f_vals = np.sum(f_samples * f['Peso'].values, axis=1)
    else:
        f_vals = np.zeros(n)
        
    if not d.empty:
        d_samples = np.random.normal(d['Calificación'].values, 0.45, size=(n, len(d)))
        d_vals = np.sum(d_samples * d['Peso'].values, axis=1)
    else:
        d_vals = np.zeros(n)
        
    if not o.empty:
        o_samples = np.random.normal(o['Calificación'].values, 0.45, size=(n, len(o)))
        o_vals = np.sum(o_samples * o['Peso'].values, axis=1)
    else:
        o_vals = np.zeros(n)
        
    if not a.empty:
        a_samples = np.random.normal(a['Calificación'].values, 0.45, size=(n, len(a)))
        a_vals = np.sum(a_samples * a['Peso'].values, axis=1)
    else:
        a_vals = np.zeros(n)
        
    x_vals = (f_vals - d_vals) * 10 - stress_interno
    y_vals = (o_vals - a_vals) * 10 - stress_externo
    
    return np.column_stack((x_vals, y_vals))

def probabilidad_exito(resultados):
    """Calcula el porcentaje de escenarios en el cuadrante Ofensivo (X > 0, Y > 0)."""
    exitos = np.sum((resultados[:, 0] > 0) & (resultados[:, 1] > 0))
    return round(exitos / len(resultados) * 100, 2)

def nivel_riesgo(prob):
    """Clasificación de riesgo de la simulación sin corchetes."""
    if prob > 70: return "BAJO RIESGO OPERACIONAL"
    elif prob > 40: return "RIESGO MODERADO - MONITOREO"
    else: return "ALTO RIESGO ESTRATÉGICO"

def mutar(df, escala=0.1):
    if df.empty: return df
    df2 = df.copy()
    ruido = np.random.normal(0, escala, size=len(df2))
    df2['Calificación'] = np.clip(df2['Calificación'] + ruido, 1.0, 5.0)
    return df2

def fitness(df_f, df_d, df_o, df_a):
    f = np.sum(df_f['Peso'] * df_f['Calificación']) if not df_f.empty else 0
    d = np.sum(df_d['Peso'] * df_d['Calificación']) if not df_d.empty else 0
    o = np.sum(df_o['Peso'] * df_o['Calificación']) if not df_o.empty else 0
    a = np.sum(df_a['Peso'] * df_a['Calificación']) if not df_a.empty else 0
    return (f - d) + (o - a)

@st.cache_data(max_entries=10, ttl=300)
def optimizar(df_f, df_d, df_o, df_a, iteraciones=200):
    """Algoritmo de búsqueda local vectorizado para maximizar balance con rendimiento ultra-rápido."""
    f = sanitizar_dataframe(df_f)
    d = sanitizar_dataframe(df_d)
    o = sanitizar_dataframe(df_o)
    a = sanitizar_dataframe(df_a)
    
    # Extraer pesos y calificaciones como numpy arrays
    w_f = f['Peso'].values
    c_f = f['Calificación'].values
    
    w_d = d['Peso'].values
    c_d = d['Calificación'].values
    
    w_o = o['Peso'].values
    c_o = o['Calificación'].values
    
    w_a = a['Peso'].values
    c_a = a['Calificación'].values
    
    best_c_f = c_f.copy()
    best_c_d = c_d.copy()
    best_c_o = c_o.copy()
    best_c_a = c_a.copy()
    
    def calc_score(cf, cd, co, ca):
        sf = np.sum(w_f * cf) if len(cf) > 0 else 0
        sd = np.sum(w_d * cd) if len(cd) > 0 else 0
        so = np.sum(w_o * co) if len(co) > 0 else 0
        sa = np.sum(w_a * ca) if len(ca) > 0 else 0
        return (sf - sd) + (so - sa)
        
    mejor_score = calc_score(best_c_f, best_c_d, best_c_o, best_c_a)
    
    escala = 0.1
    for _ in range(iteraciones):
        cf_cand = np.clip(best_c_f + np.random.normal(0, escala, size=len(best_c_f)), 1.0, 5.0) if len(best_c_f) > 0 else best_c_f
        cd_cand = np.clip(best_c_d + np.random.normal(0, escala, size=len(best_c_d)), 1.0, 5.0) if len(best_c_d) > 0 else best_c_d
        co_cand = np.clip(best_c_o + np.random.normal(0, escala, size=len(best_c_o)), 1.0, 5.0) if len(best_c_o) > 0 else best_c_o
        ca_cand = np.clip(best_c_a + np.random.normal(0, escala, size=len(best_c_a)), 1.0, 5.0) if len(best_c_a) > 0 else best_c_a
        
        score = calc_score(cf_cand, cd_cand, co_cand, ca_cand)
        if score > mejor_score:
            best_c_f, best_c_d, best_c_o, best_c_a = cf_cand, cd_cand, co_cand, ca_cand
            mejor_score = score
            
    # Reconstruir DataFrames resultantes
    f_res = f.copy()
    if not f_res.empty: f_res['Calificación'] = best_c_f
    
    d_res = d.copy()
    if not d_res.empty: d_res['Calificación'] = best_c_d
    
    o_res = o.copy()
    if not o_res.empty: o_res['Calificación'] = best_c_o
    
    a_res = a.copy()
    if not a_res.empty: a_res['Calificación'] = best_c_a
    
    return (f_res, d_res, o_res, a_res), round(mejor_score, 3)

