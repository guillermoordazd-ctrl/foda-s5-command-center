"""
STRATCOM S-5 COMMAND - HUD Futurista Mejorado
Requiere: streamlit, pandas, plotly, requests (y Ollama ejecutándose en localhost:11434)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, date, timedelta

# --- CONFIGURACIÓN DE PÁGINA HUD ---
st.set_page_config(page_title="FODA INTELIGENTE", page_icon="my_foda_s5.ico", layout="wide", initial_sidebar_state="collapsed")

def apply_tactical_style():
    """
    Inyecta CSS, fuentes y elementos estructurales para simular un HUD táctico.
    """
    st.markdown("""
    <style>
        /* ========== FUENTES ========== */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=JetBrains+Mono:wght@300;600&display=swap');

        /* ========== ESTILO GLOBAL ========== */
        .main {
            background-color: #020617;
            color: #00f2ff;
            font-family: 'Share Tech Mono', 'JetBrains Mono', monospace;
        }
        .stApp {
            background: radial-gradient(circle at center, #0f172a 0%, #020617 100%);
            position: relative;
            z-index: 1;
        }

        /* ========== OVERLAY PERMANENTE: SCANLINES + REJILLA ========== */
        /* Este div lo creamos vía st.markdown al principio de main() */
        .hud-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 9999;
            /* Scanlines (líneas horizontales cada 4px) */
            background: repeating-linear-gradient(
                to bottom,
                rgba(0, 255, 255, 0.03) 0px,
                rgba(0, 255, 255, 0.03) 1px,
                transparent 1px,
                transparent 4px
            );
        }
        .hud-overlay::after {
            content: "";
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            /* Rejilla sutil */
            background-image:
                linear-gradient(rgba(0, 242, 255, 0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 242, 255, 0.08) 1px, transparent 1px);
            background-size: 60px 60px;
            opacity: 0.5;
        }

        /* ========== CABECERA HUD ========== */
        .hud-header {
            background: rgba(2, 6, 23, 0.85);
            backdrop-filter: blur(5px);
            border-bottom: 1px solid #00f2ff;
            padding: 10px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #00f2ff;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 2px;
            font-size: 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            margin: -15px -15px 20px -15px;  /* compensar padding de Streamlit */
        }
        .hud-header .left {
            font-weight: 700;
            color: #00f2ff;
            text-shadow: 0 0 10px #00f2ff;
        }
        .hud-header .center {
            font-size: 18px;
            font-weight: 900;
            color: #fff;
            text-shadow: 0 0 15px #00f2ff;
        }
        .hud-header .right {
            display: flex;
            gap: 20px;
        }
        .alert-level {
            color: #ffaa00;
            text-shadow: 0 0 8px #ffaa00;
        }
        .alert-level.critical {
            color: #ff0055;
            text-shadow: 0 0 12px #ff0055;
        }

        /* ========== PANEL TÁCTICO (cajas) ========== */
        .hud-panel {
            border: 1px solid #00f2ff;
            background: rgba(0, 242, 255, 0.03);
            padding: 20px;
            border-radius: 2px;
            margin-bottom: 20px;
            box-shadow: inset 0 0 15px rgba(0, 242, 255, 0.1);
            position: relative;
        }
        .hud-panel::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(0deg, rgba(0,242,255,0.02) 0px, rgba(0,242,255,0.02) 2px, transparent 2px, transparent 4px);
            pointer-events: none;
        }

        /* ========== GLOW SOBRE TÍTULOS ========== */
        h1, h2, h3 {
            text-shadow: 0 0 15px #00f2ff;
        }

        /* ========== DATOS DE TABLAS (DATA EDITOR) ========== */
        /* Streamlit envuelve el editor en divs con data-testid */
        [data-testid="stDataEditor"] {
            background: rgba(0, 0, 0, 0.7) !important;
            border: 1px solid #00f2ff !important;
            font-family: 'Share Tech Mono', 'JetBrains Mono', monospace !important;
            color: #e2e8f0 !important;
        }
        [data-testid="stDataEditor"] thead th {
            background-color: #0f172a !important;
            color: #00f2ff !important;
            text-shadow: 0 0 8px #00f2ff;
            border-bottom: 1px solid #00f2ff !important;
        }

        /* ========== BOTÓN PRINCIPAL ========== */
        .stButton>button {
            border: 1px solid #00f2ff !important;
            background: rgba(0, 242, 255, 0.1) !important;
            color: #00f2ff !important;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: bold !important;
            width: 100%;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .stButton>button:hover {
            background: rgba(0, 242, 255, 0.25) !important;
            box-shadow: 0 0 20px #00f2ff;
            transform: scale(1.02);
        }
        .stButton>button:active {
            transform: scale(0.98);
        }

        /* Animación de pulso para cuando está cargando */
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 5px #00f2ff; }
            50% { box-shadow: 0 0 25px #00f2ff; }
            100% { box-shadow: 0 0 5px #00f2ff; }
        }
        .stButton>button.process {
            animation: pulseGlow 1.5s infinite;
        }

        /* ========== CAJA DE SALIDA DE IA ========== */
        .ia-output-box {
            border-left: 3px solid #ff0055;
            padding: 20px;
            background: rgba(255, 0, 85, 0.05);
            text-align: justify;
            color: #e2e8f0;
            white-space: pre-wrap;
            font-family: 'Share Tech Mono', 'JetBrains Mono', monospace;
            text-shadow: 0 0 3px rgba(255,0,85,0.3);
        }

        /* ========== AJUSTE DE COLUMNAS ========== */
        div[data-testid="column"] {
            padding: 0 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def crear_cabecera_hud(perfil_actual, nivel_alerta="AMARILLO"):
    """
    Construye el HTML de la cabecera táctica.
    Se llama en cada render, pero el estado se puede pasar por session_state.
    """
    ahora = datetime.utcnow().strftime("%H:%M:%S") + "Z"
    clase_alerta = "critical" if nivel_alerta == "ROJO" else ""
    return f"""
    <div class="hud-header">
        <div class="left">🛰️ JOPNAV S-5</div>
        <div class="center">MISIÓN: {perfil_actual.upper()}</div>
        <div class="right">
            <div class="alert-level {clase_alerta}">⚠ NIVEL {nivel_alerta}</div>
            <div>⏱️ {ahora}</div>
        </div>
    </div>
    """

# --- FUNCIÓN DEL MOTOR DE IA (PROMPT MAESTRO) ---
def ejecutar_motor_ia(perfil, tipo_analisis, foda_data, fecha_i, fecha_t):
    """Llamada a Ollama con el System Prompt Militar Integrado"""
    system_prompt = f"""
    MODO: ACTUAR COMO SISTEMA DE INTELIGENCIA ESTRATÉGICA NAVAL S-5.
    OBJETIVO: Generar diagnósticos FODA, matrices CAME y Rutas Críticas con estética HUD Militar y simbología futurista.
    PERFIL SELECCIONADO: {perfil}
    TIPO DE ANÁLISIS: {tipo_analisis}
    VENTANA TEMPORAL: {fecha_i} a {fecha_t}

    DIRECTIVAS DE FORMATO (ESTRICTAS):
    1. Tipografía y Estilo: Texto siempre Justificado.
    2. Panorama General: Párrafo breve (máximo 4 líneas) sobre el panorama estratégico detectado.
    3. Simbología de Viñetas:
       - Títulos: [NOMBRE DE SECCIÓN]
       - Puntos principales: ➣ [Punto Analizado]
       - Sub-puntos: ➢ [Detalle]
    4. Numeración: Utiliza números arábigos (1., 2., 3.) para prioridades.
    5. Estrategias CAME: Generar líneas de acción para Corregir, Afrontar, Mantener y Explotar.
    """
    user_payload = f"DATOS FODA PARA PROCESAR: {foda_data}"
    try:
        response = requests.post("http://localhost:11434/api/generate", 
            json={
                "model": "llama3",
                "prompt": system_prompt + "\n\n" + user_payload,
                "system": system_prompt,
                "stream": False
            }, timeout=45)
        return response.json().get('response', "Error: No se recibió respuesta del núcleo de IA.")
    except Exception as e:
        return f"CRITICAL ERROR: No se pudo conectar con Ollama. ({str(e)})"

# --- INTERFAZ PRINCIPAL ---
def main():
    apply_tactical_style()

    # Inicialización de datos FODA
    if 'data_foda' not in st.session_state:
        st.session_state.data_foda = {
            "F": [{"Factor": "Capacidad Táctica", "Peso": 0.25, "Calificación": 4}],
            "D": [{"Factor": "Brecha Tecnológica", "Peso": 0.25, "Calificación": 2}],
            "O": [{"Factor": "Nuevas Alianzas", "Peso": 0.25, "Calificación": 3}],
            "A": [{"Factor": "Incursiones Digitales", "Peso": 0.25, "Calificación": 1}]
        }
    if 'nivel_alerta' not in st.session_state:
        st.session_state.nivel_alerta = "AMARILLO"

    # --- OVERLAY SIEMPRE PRESENTE (scanlines + rejilla) ---
    st.markdown('<div class="hud-overlay"></div>', unsafe_allow_html=True)

    # --- CABECERA HUD DINÁMICA ---
    perfil_actual = st.session_state.get("perfil", "Sin perfil")
    st.markdown(crear_cabecera_hud(perfil_actual, st.session_state.nivel_alerta), unsafe_allow_html=True)

    # --- TÍTULO PRINCIPAL ---
    st.markdown("<h1 style='text-align:center; font-family:Orbitron; color:#00f2ff; letter-spacing:5px; text-shadow: 0 0 25px #00f2ff;'>STRATCOM S-5 COMMAND</h1>", unsafe_allow_html=True)

    # --- PANEL DE CONTROL IA ---
    with st.container():
        st.markdown('<div class="hud-panel">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            perfil = st.selectbox("👤 PERFIL", ["Sin perfil", "Inteligencia", "Operaciones", "Logística", "Planes"], key="perfil")
        with c2:
            tipo_ana = st.selectbox("🔬 TIPO DE ANÁLISIS", [
                "Análisis Militar", "Análisis Político", "Análisis Ciberespacial", 
                "Análisis Profundo", "Análisis Económico/Militar", "Análisis Político/Social"
            ])
        with c3:
            f_inicio = st.date_input("📅 INICIO RUTA", date.today())
        with c4:
            f_fin = st.date_input("📅 TÉRMINO RUTA", date.today() + timedelta(days=60))
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ZONA DE DATOS FODA ---
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**FORTALEZAS [F]**")
        df_f = st.data_editor(
            pd.DataFrame(st.session_state.data_foda["F"]),
            num_rows="dynamic",
            key="tab_f"
        )
        st.markdown("**DEBILIDADES [D]**")
        df_d = st.data_editor(
            pd.DataFrame(st.session_state.data_foda["D"]),
            num_rows="dynamic",
            key="tab_d"
        )
    with col_r:
        st.markdown("**OPORTUNIDADES [O]**")
        df_o = st.data_editor(
            pd.DataFrame(st.session_state.data_foda["O"]),
            num_rows="dynamic",
            key="tab_o"
        )
        st.markdown("**AMENAZAS [A]**")
        df_a = st.data_editor(
            pd.DataFrame(st.session_state.data_foda["A"]),
            num_rows="dynamic",
            key="tab_a"
        )

    st.markdown("---")

    # --- BOTÓN DE EJECUCIÓN CON ANIMACIÓN ---
    ejecutar = st.button("⚡ EJECUTAR INTELIGENCIA ESTRATÉGICA")
    if ejecutar:
        with st.spinner("Procesando vectores de inteligencia..."):
            # Cambiar la clase del botón para pulso (necesitaríamos JS para esto; lo simulamos con feedback visual)
            foda_context = {
                "Fortalezas": df_f.to_dict('records'),
                "Debilidades": df_d.to_dict('records'),
                "Oportunidades": df_o.to_dict('records'),
                "Amenazas": df_a.to_dict('records')
            }
            resultado = ejecutar_motor_ia(perfil, tipo_ana, foda_context, f_inicio, f_fin)

            # Actualizar nivel de alerta ficticio según resultado (ej. si contiene "crítico")
            if "crítico" in resultado.lower() or "alto riesgo" in resultado.lower():
                st.session_state.nivel_alerta = "ROJO"
            else:
                st.session_state.nivel_alerta = "AMARILLO"

        # Mostrar resultado
        st.markdown(f"### 📡 INFORME GENERADO: {tipo_ana.upper()}")
        st.markdown(f'<div class="ia-output-box">{resultado}</div>', unsafe_allow_html=True)

    # --- BOTONES DE EXPORTACIÓN ---
    st.markdown("---")
    exp_col1, exp_col2, exp_col3 = st.columns([1,1,1])
    with exp_col1:
        fmt = st.radio("Formato de Salida", ["PDF", "EXCEL"], horizontal=True, key="fmt")
    with exp_col2:
        if st.button("🖨️ IMPRIMIR GRÁFICAS"):
            st.info(f"Exportando Gráficas en {fmt} (A4 Horizontal)...")
    with exp_col3:
        if st.button("📄 IMPRIMIR ANÁLISIS"):
            st.info(f"Exportando Análisis en {fmt} (Hoja Única)...")

if __name__ == "__main__":
    main()