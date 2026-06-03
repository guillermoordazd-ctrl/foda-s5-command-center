import sqlite3
import json
from datetime import datetime
import streamlit as st

DB_PATH = "stratcom_analyses.db"

def init_db():
    """Crea la tabla de análisis si no existe."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS analyses 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       timestamp TEXT, perfil TEXT, tipo TEXT, 
                       foda_data TEXT, score_x REAL, score_y REAL)''')
        conn.commit()

def save_analysis(perfil, tipo, foda_dict, x, y):
    """Guarda un nuevo análisis en la base de datos."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO analyses (timestamp, perfil, tipo, foda_data, score_x, score_y) VALUES (?,?,?,?,?,?)",
                  (datetime.now().isoformat(), perfil, tipo, json.dumps(foda_dict), x, y))
        conn.commit()
    get_all_analyses.clear()

@st.cache_data
def get_all_analyses():
    """Recupera todos los análisis históricos guardados en la base de datos sqlite."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, timestamp, perfil, tipo, foda_data, score_x, score_y FROM analyses ORDER BY id DESC")
        return [dict(row) for row in c.fetchall()]

def clear_all_analyses():
    """Borra todos los análisis históricos."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM analyses")
        conn.commit()
    get_all_analyses.clear()