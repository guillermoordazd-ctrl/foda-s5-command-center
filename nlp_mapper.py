import pandas as pd
import re

SYNONYMS = {
    "fortalezas": [
        "fortaleza", "fortalezas", "strengths", "strength", "puntos fuertes", "fuerzas", "activos", 
        "ventajas", "superioridad", "superioridad estrategica", "ventaja tactica", "ventajas tacticas", 
        "capacidad operativa", "capacidades operativas", "capacidades", "competencias clave", 
        "puntos clave", "potencialidades", "recursos", "eficiencia"
    ],
    "debilidades": [
        "debilidad", "debilidades", "weaknesses", "weakness", "puntos debiles", "debil", "pasivos", 
        "desventajas", "vulnerabilidades", "vulnerabilidad", "deficiencias", "deficiencia", 
        "vulnerabilidades estrategicas", "vulnerabilidad estrategica", "debilidades tacticas", "debilidad tactica",
        "fallas de proceso", "falla de proceso", "limitaciones", "limitacion", "carencias", "carencia", 
        "obstaculos internos", "obstaculo interno", "puntos criticos", "punto critico", "fallos", "fallo", "ineficiencia"
    ],
    "oportunidades": [
        "oportunidad", "oportunidades", "opportunities", "opportunity", "potencial", "opciones", "mejoras", 
        "beneficios", "oportunidades de mercado", "oportunidad de mercado", "oportunidades estrategicas", 
        "oportunidad estrategica", "areas de oportunidad", "area de oportunidad", "potencial operativo", 
        "factores de crecimiento", "escenarios favorables", "desarrollo", "tendencias positivas", "tendencia positiva"
    ],
    "amenazas": [
        "amenaza", "amenazas", "threats", "threat", "riesgos", "riesgo", "peligros", "peligro", "desafios", "desafio", 
        "contingencias", "contingencia", "adversidades", "adversidad", "amenazas globales", "amenaza global", 
        "amenazas externas", "amenaza externa", "riesgos operativos", "riesgo operativo", "riesgos tacticos", "riesgo tactico",
        "peligros inmediatos", "peligro inmediato", "barreras", "barrera", "presiones externas", "presion externa", 
        "factores de riesgo", "factor de riesgo"
    ]
}

def normalize(text):
    text = text.lower().strip()
    text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    return text

def map_columns_to_foda(df):
    mapping = {key: None for key in SYNONYMS.keys()}
    columns = df.columns.tolist()
    for col in columns:
        norm_col = normalize(col)
        for key, synonyms in SYNONYMS.items():
            if mapping[key] is None:
                for syn in synonyms:
                    if syn in norm_col or norm_col in syn:
                        mapping[key] = col
                        break
    return mapping