import plotly.graph_objects as go
import numpy as np
import pandas as pd
import textwrap
from typing import NamedTuple

def grafico_evolucion(hist):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist[:, 0], y=hist[:, 1], name="Interno (X)", line=dict(color='#00f2ff', width=3)))
    fig.add_trace(go.Scatter(x=hist[:, 0], y=hist[:, 2], name="Externo (Y)", line=dict(color='#39FF14', width=3)))
    fig.update_layout(
        title="Proyección de Evolución del Vector (12 Periodos)",
        paper_bgcolor='rgba(2, 6, 23, 0.8)', plot_bgcolor='rgba(2, 6, 23, 0.8)',
        font=dict(color='#39FF14', family='Share Tech Mono'),
        xaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)', title="Periodos (t)"),
        yaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)', title="Magnitud"),
        margin=dict(l=40, r=40, t=40, b=40), height=350
    )
    return fig

def grafico_simulacion(resultados):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=resultados[:, 0], y=resultados[:, 1],
        mode='markers', marker=dict(size=4, color='#39FF14', opacity=0.25),
        name="Escenarios"
    ))
    # Resaltar el centro
    fig.add_shape(type="line", x0=-50, y0=0, x1=50, y1=0, line=dict(color="rgba(0, 242, 255, 0.3)", width=1, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-50, x1=0, y1=50, line=dict(color="rgba(0, 242, 255, 0.3)", width=1, dash="dash"))
    
    fig.update_layout(
        paper_bgcolor='rgba(2, 6, 23, 0.8)', plot_bgcolor='rgba(2, 6, 23, 0.8)',
        font=dict(color='#39FF14', family='Share Tech Mono'),
        title="Dispersión estocástica de escenarios Monte Carlo",
        xaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)', range=[-50, 50]),
        yaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)', range=[-50, 50]),
        margin=dict(l=40, r=40, t=40, b=40), height=350,
        showlegend=False
    )
    return fig

def radar_estrategico(scores):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[scores["F"], scores["O"], scores["D"], scores["A"], scores["F"]],
        theta=['Fortalezas', 'Oportunidades', 'Debilidades', 'Amenazas', 'Fortalezas'],
        fill='toself',
        fillcolor='rgba(0, 242, 255, 0.15)',
        line=dict(color='#00f2ff', width=2)
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(2, 6, 23, 0.8)',
            radialaxis=dict(visible=True, gridcolor='rgba(0, 242, 255, 0.15)', linecolor='rgba(0, 242, 255, 0.3)'),
            angularaxis=dict(gridcolor='rgba(0, 242, 255, 0.15)', linecolor='rgba(0, 242, 255, 0.3)')
        ),
        paper_bgcolor='rgba(2, 6, 23, 0.8)',
        font=dict(color='#00f2ff', family='Share Tech Mono'),
        margin=dict(l=40, r=40, t=40, b=40), height=350
    )
    return fig

def barras_balance(scores):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Fortalezas', 'Debilidades', 'Oportunidades', 'Amenazas'],
        y=[scores["F"], scores["D"], scores["O"], scores["A"]],
        marker_color=['#39FF14', '#ff0055', '#39FF14', '#ff0055'],
        marker_line=dict(width=1.5, color='#ffffff')
    ))
    fig.update_layout(
        paper_bgcolor='rgba(2, 6, 23, 0.8)', plot_bgcolor='rgba(2, 6, 23, 0.8)',
        font=dict(color='#39FF14', family='Share Tech Mono'),
        xaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)'),
        yaxis=dict(gridcolor='rgba(57, 255, 20, 0.1)'),
        margin=dict(l=40, r=40, t=40, b=40), height=350
    )
    return fig

def grafico_posicionamiento(x, y):
    """Dibuja el plano cartesiano estratégico con el punto estratégico HUD."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[x], y=[y], mode='markers+text',
        marker=dict(size=16, color='#00f2ff', symbol='cross', line=dict(width=2, color='#ffffff')),
        text=[f"COORDENADA ESTRATÉGICA ({x}, {y})"], textposition="top center",
        textfont=dict(color='#00f2ff', size=11, family='Orbitron'),
        name="Vector Resultante"
    ))
    
    # Líneas divisorias de cuadrantes
    fig.add_shape(type="line", x0=-50, y0=0, x1=50, y1=0, line=dict(color="#39FF14", width=1.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-50, x1=0, y1=50, line=dict(color="#39FF14", width=1.5, dash="dash"))
    
    # Tonalidad de cuadrantes
    fig.add_hrect(y0=0, y1=50, line_width=0, fillcolor="rgba(0, 242, 255, 0.03)", layer="below")
    fig.add_hrect(y0=-50, y1=0, line_width=0, fillcolor="rgba(255, 0, 85, 0.03)", layer="below")
    fig.add_vrect(x0=0, x1=50, line_width=0, fillcolor="rgba(57, 255, 20, 0.03)", layer="below")
    fig.add_vrect(x0=-50, x1=0, line_width=0, fillcolor="rgba(255, 170, 0, 0.03)", layer="below")
    
    fig.update_layout(
        xaxis=dict(title="SITUACIÓN INTERNA (X)", range=[-50, 50], gridcolor="rgba(57, 255, 20, 0.1)", zeroline=False),
        yaxis=dict(title="SITUACIÓN EXTERNA (Y)", range=[-50, 50], gridcolor="rgba(57, 255, 20, 0.1)", zeroline=False),
        plot_bgcolor="#020617", paper_bgcolor="#020617",
        font=dict(color="#39FF14", family="Share Tech Mono"),
        margin=dict(l=40, r=40, t=40, b=40), height=450
    )
    return fig

def crear_diagrama_ishikawa(df_d, df_a, estado_actual):
    """
    Construye un diagrama causa-efecto Ishikawa (espina de pescado) dinámico.
    Asigna Debilidades a Huesos Internos (Tecnología, Procesos, Personal)
    y Amenazas a Huesos Externos (Entorno).
    """
    fig = go.Figure()
    
    # Eje Central (Espina Dorsal)
    fig.add_trace(go.Scatter(
        x=[0, 10], y=[0, 0],
        mode='lines+markers',
        line=dict(color='#00f2ff', width=4),
        marker=dict(size=8, color='#00f2ff'),
        showlegend=False
    ))
    
    # Cabeza del Pescado (Efecto)
    label_cabeza = estado_actual.replace("[ESTADO: ", "").replace("]", "")
    fig.add_trace(go.Scatter(
        x=[10.5], y=[0],
        mode='markers+text',
        marker=dict(size=25, color='#ff0055', symbol='diamond'),
        text=[f"  EFECTO:<br>  {label_cabeza}"],
        textposition="middle right",
        textfont=dict(color='#ff0055', size=10, family='Orbitron'),
        showlegend=False,
        cliponaxis=False
    ))
    
    # Definición de estructura tipada para las espinas principales
    class Espina(NamedTuple):
        nombre: str
        x_start: float
        x_end: float
        y_end: float
        color: str

    # Espinas principales (Huesos del pescado)
    espinas = [
        Espina("TECNOLOGÍA", 2.0, 4.0, 3.0, "#00f2ff"),
        Espina("PROCESOS",   6.0, 8.0, 3.0, "#39FF14"),
        Espina("PERSONAL",   2.0, 4.0, -3.0, "#ffaa00"),
        Espina("ENTORNO",    6.0, 8.0, -3.0, "#ff0055")
    ]
    
    for esp in espinas:
        # Línea de la espina
        fig.add_trace(go.Scatter(
            x=[esp.x_start, esp.x_end], y=[0.0, esp.y_end],
            mode='lines+text',
            line=dict(color=esp.color, width=2.5),
            text=[None, f" {esp.nombre}"],
            textposition="top center" if esp.y_end > 0 else "bottom center",
            textfont=dict(color=esp.color, size=10, family='Orbitron'),
            showlegend=False,
            cliponaxis=False
        ))
        
    # Clasificar factores reales ingresados por el usuario
    debilidades = df_d['Factor'].tolist() if not df_d.empty else []
    amenazas = df_a['Factor'].tolist() if not df_a.empty else []
    
    cat_data = {
        "TECNOLOGÍA": [],
        "PROCESOS": [],
        "PERSONAL": [],
        "ENTORNO": []
    }
    
    tech_keywords = [
        "tecnolog", "sist", "cyber", "ciber", "software", "digital", "herramienta", "base de datos", "db", 
        "enlace", "tecnologica", "hardware", "red", "infraestructura", "servidor", "cloud", "nube", 
        "aplicacion", "app", "codigo", "plataforma", "ciberseguridad", "cifrado", "encriptado", 
        "automatizacion", "computo", "firewall", "router", "telecom", "soporte", "plataformas",
        "comunic", "telemetr", "radar", "sonar", "c4i", "c2", "c4isr", "c3", "satelital", "inhibidor",
        "jamming", "ew", "dron", "uav", "rpas", "blindado", "armamento", "fuego", "bateria", "cripto",
        "gps", "posicionamiento", "simulador", "sensores", "optronica", "sonar", "infrarrojo", "vision nocturna", "optica",
        "antivirus", "protocolo", "exploit", "negacion", "ip", "informatico",
        "navio", "remolcador", "fragata", "corbeta", "destructor", "submarino", "minas", "dragaminas",
        "desminado", "artefacto", "explosivo", "vehiculo", "intercepcion",
        "tanque", "tanques", "misil", "misiles", "cohete", "cohetes", "satelite",
        "avion", "aviones", "helicoptero", "helicopteros", "buque", "buques",
        "espectro", "electromagnetico", "cibernetico", "municion",
        "balistica", "senuelo", "dummy", "ciberespacio", "mina",
        "malware", "memoria ram", "browser", "navegador", "computadora", "internet", "intranet", "big data",
        "bigdata", "algoritmo", "inteligencia artificial", "artificial intelligence", "cache",
        "comercio electronico", "binario", "hashtag", "plugin",
        "guerra electronica"
    ]

    pers_keywords = [
        "person", "capacit", "entrena", "humano", "operador", "empleado", "equipo", "lider", "liderazgo", 
        "brecha", "talento", "recursos humanos", "rrhh", "tropa", "soldado", "comandante", "tripulacion", 
        "staff", "reclutamiento", "competencias", "habilidad", "destreza", "formacion", "instruccion", 
        "vacante", "sueldo", "salario", "plantilla", "vacantes", "nomina", "incentivo", "fatiga", "capacitacion", "estres",
        "oficial", "suboficial", "combatiente", "efectivo", "militares", "uniformados", "moral", "disciplina",
        "lealtad", "cohesion", "bajas", "reemplazo", "dotacion", "postraumatico", "ptsd", "adestramiento",
        "maniobras", "ejercicios", "simulacros", "combate", "detacamento", "patrulla", "peloton", "compania",
        "batallon", "brigada", "escalafon", "especialidad", "cadete", "desgaste",
        "almirante", "capitan", "jefe", "alumno", "especialista", "fuerzas especiales", "fuerzas navales",
        "ingenieros", "civiles", "desercion", "abandono",
        "sargento", "cabo", "marinero", "maestre", "paracaidista", "director", "directivo",
        "jefe de unidad", "policia", "licenciado", "arquitecto", "marineria"
    ]

    def strip_accents(text):
        if not text:
            return ""
        text = text.lower().strip()
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        return text

    for deb in debilidades:
        deb_norm = strip_accents(deb)
        if any(ex in deb_norm for ex in ["derechos humanos", "derecho internacional"]):
            cat_data["PROCESOS"].append(deb)
        elif any(w in deb_norm for w in tech_keywords):
            cat_data["TECNOLOGÍA"].append(deb)
        elif any(w in deb_norm for w in pers_keywords):
            cat_data["PERSONAL"].append(deb)
        else:
            cat_data["PROCESOS"].append(deb)

    for am in amenazas:
        am_norm = strip_accents(am)
        if any(w in am_norm for w in tech_keywords):
            cat_data["TECNOLOGÍA"].append(am)
        elif any(w in am_norm for w in pers_keywords):
            cat_data["PERSONAL"].append(am)
        else:
            cat_data["ENTORNO"].append(am)
            
    # Rellenar con vacíos si no hay datos
    for cat in cat_data:
        if not cat_data[cat]:
            cat_data[cat] = ["Sin incidencias registradas"]
            
    # Dibujar causas secundarias (espinas laterales)
    for esp in espinas:
        nombre = esp.nombre
        factores = cat_data.get(nombre, [])
        y_end = esp.y_end
        x_start = esp.x_start
        x_end = esp.x_end
        is_left = (x_start < 5.0)
        
        for idx, fact in enumerate(factores[:3]):
            # Posición a lo largo del hueso
            frac = 0.3 + 0.25 * idx
            x_pos = x_start + (x_end - x_start) * frac
            y_pos = y_end * frac
            
            # Espina secundaria horizontal (izq hacia la izquierda, der hacia la derecha)
            if is_left:
                x_line_end = x_pos - 1.4
                text_pos = "middle left"
                wrapped_text = "<br>".join(textwrap.wrap(fact, width=32))
                text_content = [None, wrapped_text + "  "]
            else:
                x_line_end = x_pos + 1.4
                text_pos = "middle right"
                wrapped_text = "<br>".join(textwrap.wrap(fact, width=32))
                text_content = [None, "  " + wrapped_text]
                
            fig.add_trace(go.Scatter(
                x=[x_pos, x_line_end], y=[y_pos, y_pos],
                mode='lines+text',
                line=dict(color=esp.color, width=1, dash="dot"),
                text=text_content,
                textposition=text_pos,
                textfont=dict(color='#e2e8f0', size=10, family='Share Tech Mono'),
                showlegend=False,
                cliponaxis=False
            ))
            
    fig.update_layout(
        plot_bgcolor='#020617', paper_bgcolor='#020617',
        xaxis=dict(visible=False, range=[-6.5, 17.5]),
        yaxis=dict(visible=False, range=[-4.5, 4.5]),
        margin=dict(l=15, r=15, t=15, b=15),
        height=620
    )
    return fig
