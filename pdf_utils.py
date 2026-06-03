from fpdf import FPDF
import io
import re
from datetime import datetime
import pandas as pd
import numpy as np
from models import simulacion_montecarlo, simular_periodos, clasificacion, decidir, optimizar


class TacticalPDF(FPDF):
    def header(self):
        # Fondo oscuro táctico militar para cada página (Carta Apaisado: 279.4 x 215.9 mm)
        self.set_fill_color(2, 6, 23)
        self.rect(0, 0, 279.4, 215.9, 'F')
        
        # Título del HUD
        self.set_font('Courier', 'B', 12)
        self.set_text_color(0, 242, 255)
        self.cell(0, 8, 'FODA JOPNAV S5 // INFORME ESTRATÉGICO E-INFORME', 0, 0, 'L')
        
        self.set_font('Courier', 'B', 9)
        self.set_text_color(57, 255, 20)
        self.cell(0, 8, 'ESTADO: OPERACIONAL', 0, 1, 'R')
        
        # Línea de separación HUD (Verde neón ajustada a ancho Carta: 279.4 - 10 = 269.4)
        self.set_draw_color(57, 255, 20)
        self.set_line_width(0.5)
        self.line(10, 16, 269.4, 16)
        self.ln(4)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Courier', 'I', 8)
        self.set_text_color(100, 150, 200)
        self.cell(0, 10, f'CONFIDENCIAL S-5 // HOJA {self.page_no()} DE 7', 0, 0, 'C')

def clean_pdf_string(s):
    """Sanitiza strings unicode para FPDF (Latin-1) sin remover acentos ni la letra Ñ."""
    s = str(s)
    replacements = {
        '➣': '->', '➢': '->', '◈': '*', '::': ':', '■': '*', '▒': '|',
        '🟢': '', '🔴': '', '🟡': '', '🔵': '', '🟨': '', '🟦': '', '🟥': '', '🟩': ''
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode('latin-1', 'replace').decode('latin-1')

def parse_came_text(text):
    if not text:
        return None
    
    # 1. Normalizar espaciado
    lines = [line.strip() for line in text.split('\n')]
    new_lines = []
    for line in lines:
        if not line:
            continue
        is_header = (
            re.match(r'^(1\.[^0-9]|2\.[^0-9]|3\.\s*(?:l[ií]neas|recom|accion|dirección|postura))', line, re.IGNORECASE) or
            re.match(r'^(1\.\s*(?:fortalezas|debilidades)|2\.\s*(?:oportunidades|amenazas))', line, re.IGNORECASE)
        )
        if is_header and new_lines:
            new_lines.append("")
        new_lines.append(line)
    text_normalized = "\n".join(new_lines)
    
    # 2. Agrupar por secciones
    lines = [line.strip() for line in text_normalized.split('\n') if line.strip()]
    part1_header = ""
    part1_paragraphs = []
    part2_header = ""
    part2_paragraphs = []
    recs = []
    current_part = 0
    
    for line in lines:
        is_part1_marker = (
            re.match(r'^1\.[^0-9]', line, re.IGNORECASE) or 
            "1. Fortalezas" in line or 
            "1. Debilidades" in line
        )
        is_part2_marker = (
            re.match(r'^2\.[^0-9]', line, re.IGNORECASE) or 
            "2. Oportunidades" in line or 
            "2. Amenazas" in line
        )
        is_part3_marker = (
            re.match(r'^(3\.\s*(?:l[ií]neas|recom|accion|dirección|postura)|3\.,\s*4\.)', line, re.IGNORECASE) or
            "3. LÍNEAS DE ACCIÓN" in line.upper()
        )
        
        if is_part1_marker and current_part < 1:
            current_part = 1
            match = re.match(r'^(1\.[^:]+:?)(.*)', line, re.IGNORECASE)
            if match:
                part1_header = match.group(1).strip()
                body_init = match.group(2).strip()
                if body_init:
                    part1_paragraphs.append(body_init)
            else:
                part1_header = line
            continue
        elif is_part2_marker and current_part < 2:
            current_part = 2
            match = re.match(r'^(2\.[^:]+:?)(.*)', line, re.IGNORECASE)
            if match:
                part2_header = match.group(1).strip()
                body_init = match.group(2).strip()
                if body_init:
                    part2_paragraphs.append(body_init)
            else:
                part2_header = line
            continue
        elif is_part3_marker and current_part < 3:
            current_part = 3
            continue
            
        if current_part == 1:
            part1_paragraphs.append(line)
        elif current_part == 2:
            part2_paragraphs.append(line)
        elif current_part == 3 or current_part == 0:
            cleaned_rec = re.sub(r'^\s*(?:[\*\-\+]\s+|(?:\d+[\.\)\s]*)+)', '', line).strip()
            if cleaned_rec:
                recs.append(cleaned_rec)
                
    return {
        "part1_header": part1_header,
        "part1_paragraphs": part1_paragraphs,
        "part2_header": part2_header,
        "part2_paragraphs": part2_paragraphs,
        "recs": recs
    }

def render_came_strategy_pdf(pdf, start_x, start_y, ancho, text, font_size, line_height, header_color_rgb):
    pdf.set_xy(start_x, start_y)
    
    # Early return if strategy is not formulated or too short
    text_stripped = text.strip()
    if not text_stripped or "no formulada" in text_stripped.lower() or len(text_stripped) < 15:
        pdf.set_font("Courier", 'I', font_size)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(ancho, line_height, clean_pdf_string(text_stripped), align='L')
        return
        
    parsed = parse_came_text(text)
    
    # Fallback si no tiene la estructura CAME o es muy corta
    if not parsed or (not parsed["part1_paragraphs"] and not parsed["part2_paragraphs"] and not parsed["recs"]):
        pdf.set_font("Courier", '', font_size)
        pdf.set_text_color(220, 220, 220)
        text_clean = "\n".join([line.strip() for line in text.split('\n') if line.strip()])
        pdf.multi_cell(ancho, line_height, clean_pdf_string(text_clean), align='J')
        return
        
    part1_header = parsed["part1_header"]
    part1_paragraphs = parsed["part1_paragraphs"]
    part2_header = parsed["part2_header"]
    part2_paragraphs = parsed["part2_paragraphs"]
    recs = parsed["recs"]
    
    y_current = start_y
    
    # 1. Parte 1 (Análisis Interno)
    if part1_paragraphs:
        header_display = part1_header if part1_header else "1. ANÁLISIS INTERNO"
        pdf.set_xy(start_x, y_current)
        pdf.set_font("Courier", 'B', font_size + 0.5)
        pdf.set_text_color(*header_color_rgb)
        pdf.cell(ancho, line_height + 0.5, clean_pdf_string(header_display), 0, 1)
        y_current = pdf.get_y()
        
        pdf.set_font("Courier", '', font_size)
        pdf.set_text_color(220, 220, 220)
        for idx, p in enumerate(part1_paragraphs):
            pdf.set_x(start_x)
            indent = "     " if idx > 0 else ""
            pdf.multi_cell(ancho, line_height, indent + clean_pdf_string(p), align='J')
        pdf.ln(1.0)
        y_current = pdf.get_y()
        
    # 2. Parte 2 (Análisis Externo)
    if part2_paragraphs:
        header_display = part2_header if part2_header else "2. ANÁLISIS EXTERNO"
        pdf.set_xy(start_x, y_current)
        pdf.set_font("Courier", 'B', font_size + 0.5)
        pdf.set_text_color(0, 242, 255) # Celeste táctico para externo
        pdf.cell(ancho, line_height + 0.5, clean_pdf_string(header_display), 0, 1)
        y_current = pdf.get_y()
        
        pdf.set_font("Courier", '', font_size)
        pdf.set_text_color(220, 220, 220)
        for idx, p in enumerate(part2_paragraphs):
            pdf.set_x(start_x)
            indent = "     " if idx > 0 else ""
            pdf.multi_cell(ancho, line_height, indent + clean_pdf_string(p), align='J')
        pdf.ln(1.0)
        y_current = pdf.get_y()
        
    # 3. Recomendaciones (Líneas de Acción)
    if recs:
        pdf.set_xy(start_x, y_current)
        pdf.set_font("Courier", 'B', font_size + 0.5)
        pdf.set_text_color(255, 170, 0) # Naranja/Amarillo
        pdf.cell(ancho, line_height + 0.5, "3. LÍNEAS DE ACCIÓN Y RECOMENDACIONES", 0, 1)
        y_current = pdf.get_y()
        
        old_l_margin = pdf.l_margin
        
        for idx, rec in enumerate(recs):
            num_val = idx + 1
            pdf.set_xy(start_x, y_current)
            pdf.set_font("Courier", 'B', font_size)
            pdf.set_text_color(255, 170, 0)
            pdf.write(line_height, f"{num_val}. ")
            
            pdf.set_font("Courier", '', font_size)
            pdf.set_text_color(220, 220, 220)
            
            pdf.set_left_margin(start_x + 6)
            pdf.set_xy(start_x + 6, y_current)
            pdf.multi_cell(ancho - 6, line_height, clean_pdf_string(rec), align='J')
            y_current = pdf.get_y()
            pdf.set_left_margin(old_l_margin)

def draw_cartesian_plane(pdf, x_origin, y_origin, size, x_val, y_val):
    # Fondo oscuro táctico
    pdf.set_fill_color(2, 6, 23)
    pdf.rect(x_origin, y_origin, size, size, 'F')
    
    # Rejilla
    pdf.set_draw_color(20, 35, 75)
    pdf.set_line_width(0.15)
    divisions = 10
    step = size / divisions
    for i in range(1, divisions):
        pdf.line(x_origin, y_origin + i * step, x_origin + size, y_origin + i * step)
        pdf.line(x_origin + i * step, y_origin, x_origin + i * step, y_origin + size)
        
    # Ejes centralizados (X e Y) correspondientes al punto (0,0) en el rango -50 a 50
    pdf.set_draw_color(57, 255, 20)
    pdf.set_line_width(0.4)
    # Eje X horizontal
    pdf.line(x_origin, y_origin + size/2, x_origin + size, y_origin + size/2)
    # Eje Y vertical
    pdf.line(x_origin + size/2, y_origin, x_origin + size/2, y_origin + size)
    
    # Cuadrantes
    pdf.set_font('Courier', 'B', 8)
    pdf.set_text_color(100, 150, 200)
    pdf.set_xy(x_origin + 2, y_origin + 2)
    pdf.cell(0, 0, "DO", 0, 0)
    
    pdf.set_xy(x_origin + size - 8, y_origin + 2)
    pdf.cell(0, 0, "FO", 0, 0)
    
    pdf.set_xy(x_origin + 2, y_origin + size - 4)
    pdf.cell(0, 0, "DA", 0, 0)
    
    pdf.set_xy(x_origin + size - 8, y_origin + size - 4)
    pdf.cell(0, 0, "FA", 0, 0)
    
    # Mapeo del punto estratégico
    x_px = x_origin + (x_val + 50.0) / 100.0 * size
    y_px = y_origin + (50.0 - y_val) / 100.0 * size
    
    x_px = max(x_origin, min(x_origin + size, x_px))
    y_px = max(y_origin, min(y_origin + size, y_px))
    
    # Cruz del vector resultante
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.8)
    pdf.line(x_px - 4, y_px, x_px + 4, y_px)
    pdf.line(x_px, y_px - 4, x_px, y_px + 4)
    pdf.set_fill_color(0, 242, 255)
    pdf.circle(x_px, y_px, 1.0, 'F')
    
    # Etiqueta
    pdf.set_font('Courier', 'B', 8)
    pdf.set_text_color(0, 242, 255)
    if x_px > x_origin + size * 0.7:
        pdf.set_xy(x_px - 26, y_px - 2)
    else:
        pdf.set_xy(x_px + 3, y_px - 2)
    pdf.cell(0, 0, f"({x_val:+.1f}, {y_val:+.1f})", 0, 0)
    
    # Borde
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.5)
    pdf.rect(x_origin, y_origin, size, size, 'D')

def draw_radar_chart(pdf, x_center, y_center, radius, scores):
    # Anillos concéntricos de 1.0 a 5.0
    pdf.set_draw_color(20, 35, 75)
    pdf.set_line_width(0.15)
    for r_level in range(1, 6):
        r_dist = (r_level / 5.0) * radius
        pdf.polygon([
            (x_center, y_center - r_dist),      # F (Up)
            (x_center + r_dist, y_center),      # O (Right)
            (x_center, y_center + r_dist),      # D (Down)
            (x_center - r_dist, y_center)       # A (Left)
        ], 'D')
        
    # Ejes
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.3)
    pdf.line(x_center, y_center - radius, x_center, y_center + radius) # vertical
    pdf.line(x_center - radius, y_center, x_center + radius, y_center) # horizontal
    
    # Coordenadas del polígono estratégico
    val_f = scores.get("F", 3.0)
    val_o = scores.get("O", 3.0)
    val_d = scores.get("D", 3.0)
    val_a = scores.get("A", 3.0)
    
    pts = [
        (x_center, y_center - (val_f / 5.0) * radius),
        (x_center + (val_o / 5.0) * radius, y_center),
        (x_center, y_center + (val_d / 5.0) * radius),
        (x_center - (val_a / 5.0) * radius, y_center)
    ]
    
    # Relleno del polígono
    pdf.set_fill_color(0, 80, 100)
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.8)
    pdf.polygon(pts, 'FD')
    
    # Vértices neón
    pdf.set_fill_color(57, 255, 20)
    for p_x, p_y in pts:
        pdf.circle(p_x, p_y, 1.2, 'F')
        
    # Etiquetas
    pdf.set_font('Courier', 'B', 8)
    pdf.set_text_color(57, 255, 20)
    
    # F (Up)
    pdf.set_xy(x_center - 10, y_center - radius - 5)
    pdf.cell(20, 4, f"F: {val_f:.2f}", 0, 0, 'C')
    
    # O (Right)
    pdf.set_xy(x_center + radius + 2, y_center - 2)
    pdf.cell(20, 4, f"O: {val_o:.2f}", 0, 0, 'L')
    
    # D (Down)
    pdf.set_xy(x_center - 10, y_center + radius + 2)
    pdf.cell(20, 4, f"D: {val_d:.2f}", 0, 0, 'C')
    
    # A (Left)
    pdf.set_xy(x_center - radius - 22, y_center - 2)
    pdf.cell(20, 4, f"A: {val_a:.2f}", 0, 0, 'R')

def draw_bar_chart(pdf, x_origin, y_origin, width, height, scores):
    # Fondo
    pdf.set_fill_color(2, 6, 23)
    pdf.rect(x_origin, y_origin, width, height, 'F')
    
    # Ejes
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.4)
    pdf.line(x_origin + 6, y_origin + 2, x_origin + 6, y_origin + height - 5)
    pdf.line(x_origin + 6, y_origin + height - 5, x_origin + width - 5, y_origin + height - 5)
    
    # Niveles y rejilla horizontal
    pdf.set_draw_color(20, 35, 75)
    pdf.set_line_width(0.15)
    for level in range(1, 6):
        y_pos = y_origin + height - 5 - (level / 5.0) * (height - 10)
        pdf.line(x_origin + 6, y_pos, x_origin + width - 5, y_pos)
        pdf.set_font('Courier', '', 6)
        pdf.set_text_color(100, 150, 200)
        pdf.set_xy(x_origin + 1, y_pos - 1.5)
        pdf.cell(4, 3, str(level), 0, 0, 'R')
        
    # Barras F, D, O, A
    keys = ["F", "D", "O", "A"]
    labels = ["F", "D", "O", "A"]
    colors = [
        (57, 255, 20),
        (255, 0, 85),
        (57, 255, 20),
        (255, 0, 85)
    ]
    
    num_bars = len(keys)
    bar_width = (width - 15) / num_bars - 4
    spacing = 4
    
    pdf.set_font('Courier', 'B', 8)
    for idx, key in enumerate(keys):
        val = scores.get(key, 3.0)
        bar_h = (val / 5.0) * (height - 10)
        
        bx = x_origin + 8 + idx * (bar_width + spacing)
        by = y_origin + height - 5 - bar_h
        
        # Barra
        pdf.set_fill_color(*colors[idx])
        pdf.rect(bx, by, bar_width, bar_h, 'F')
        
        # Valor sobre la barra
        pdf.set_text_color(220, 220, 220)
        pdf.set_xy(bx - 2, by - 4)
        pdf.cell(bar_width + 4, 3, f"{val:.2f}", 0, 0, 'C')
        
        # Etiqueta bajo la barra
        pdf.set_text_color(*colors[idx])
        pdf.set_xy(bx - 2, y_origin + height - 4.5)
        pdf.cell(bar_width + 4, 4, labels[idx], 0, 0, 'C')

def draw_ishikawa(pdf, x_origin, y_origin, width, height, df_d, df_a, estado_actual):
    # Fondo
    pdf.set_fill_color(2, 6, 23)
    pdf.rect(x_origin, y_origin, width, height, 'F')
    
    # Eje central (Espina Dorsal)
    spine_y = y_origin + height / 2.0
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(1.5)
    pdf.line(x_origin + 10, spine_y, x_origin + width - 45, spine_y)
    
    # Cabeza (Efecto)
    head_x = x_origin + width - 35
    pdf.set_fill_color(255, 0, 85)
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(0.5)
    pts = [
        (head_x, spine_y - 12),
        (head_x + 25, spine_y),
        (head_x, spine_y + 12),
        (head_x - 12, spine_y)
    ]
    pdf.polygon(pts, 'FD')
    
    pdf.set_font('Courier', 'B', 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(head_x - 10, spine_y - 4)
    effect_label = estado_actual.replace("ESTADO: ", "").split("(")[0].strip()
    pdf.multi_cell(32, 3.5, effect_label[:25], 0, 'C')
    
    # Espinas principales
    espinas = [
        {"nombre": "TECNOLOGÍA", "color": (0, 242, 255), "x_start": x_origin + 40,  "x_end": x_origin + 90,  "y_start": spine_y, "y_end": spine_y - 36},
        {"nombre": "PROCESOS",   "color": (57, 255, 20),  "x_start": x_origin + 120, "x_end": x_origin + 170, "y_start": spine_y, "y_end": spine_y - 36},
        {"nombre": "PERSONAL",   "color": (255, 170, 0),  "x_start": x_origin + 40,  "x_end": x_origin + 90,  "y_start": spine_y, "y_end": spine_y + 36},
        {"nombre": "ENTORNO",    "color": (255, 0, 85),   "x_start": x_origin + 120, "x_end": x_origin + 170, "y_start": spine_y, "y_end": spine_y + 36}
    ]
    
    # Clasificación de causas
    cat_data = {
        "TECNOLOGÍA": [],
        "PROCESOS": [],
        "PERSONAL": [],
        "ENTORNO": []
    }
    
    debilidades = df_d['Factor'].tolist() if not df_d.empty else []
    amenazas = df_a['Factor'].tolist() if not df_a.empty else []
    
    tech_keywords = ["tecnolog", "sist", "cyber", "ciber", "software", "digital", "herramienta", "base de datos", "db", "enlace", "tecnologica", "hardware", "red", "infraestructura", "servidor", "cloud", "nube", "aplicacion", "app", "codigo", "plataforma", "ciberseguridad", "cifrado", "encriptado", "automatizacion", "computo", "firewall", "router", "telecom", "soporte", "plataformas", "comunic", "telemetr", "radar", "sonar", "c4i", "c2", "c4isr", "c3", "satelital", "inhibidor", "jamming", "ew", "dron", "uav", "rpas", "blindado", "armamento", "fuego", "bateria", "cripto", "gps", "posicionamiento", "simulador", "sensores", "optronica", "sonar", "infrarrojo", "vision nocturna", "optica", "antivirus", "protocolo", "exploit", "negacion", "ip", "informatico", "navio", "remolcador", "fragata", "corbeta", "destructor", "submarino", "minas", "dragaminas", "desminado", "artefacto", "explosivo", "vehiculo", "intercepcion", "tanque", "tanques", "misil", "misiles", "cohete", "cohetes", "satelite", "avion", "aviones", "helicoptero", "helicopteros", "buque", "buques", "espectro", "electromagnetico", "cibernetico", "municion", "balistica", "senuelo", "dummy", "ciberespacio", "mina", "malware", "memoria ram", "browser", "navegador", "computadora", "internet", "intranet", "big data", "bigdata", "algoritmo", "inteligencia artificial", "artificial intelligence", "cache", "comercio electronico", "binario", "hashtag", "plugin", "guerra electronica"]
    pers_keywords = ["person", "capacit", "entrena", "humano", "operador", "empleado", "equipo", "lider", "liderazgo", "brecha", "talento", "recursos humanos", "rrhh", "tropa", "soldado", "comandante", "tripulacion", "staff", "reclutamiento", "competencias", "habilidad", "destreza", "formacion", "instruccion", "vacante", "sueldo", "salario", "plantilla", "vacantes", "nomina", "incentivo", "fatiga", "capacitacion", "estres", "oficial", "suboficial", "combatiente", "efectivo", "militares", "uniformados", "moral", "disciplina", "lealtad", "cohesion", "bajas", "reemplazo", "dotacion", "postraumatico", "ptsd", "adestramiento", "maniobras", "ejercicios", "simulacros", "combate", "detacamento", "patrulla", "peloton", "compania", "batallon", "brigada", "escalafon", "especialidad", "cadete", "desgaste", "almirante", "capitan", "jefe", "alumno", "especialista", "fuerzas especiales", "fuerzas navales", "ingenieros", "civiles", "desercion", "abandono", "sargento", "cabo", "marinero", "maestre", "paracaidista", "director", "directivo", "jefe de unidad", "policia", "licenciado", "arquitecto", "marineria"]

    def clean_text_for_ish(text):
        if not text:
            return ""
        text = text.lower().strip()
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        return text

    for deb in debilidades:
        deb_norm = clean_text_for_ish(deb)
        if any(ex in deb_norm for ex in ["derechos humanos", "derecho internacional"]):
            cat_data["PROCESOS"].append(deb)
        elif any(w in deb_norm for w in tech_keywords):
            cat_data["TECNOLOGÍA"].append(deb)
        elif any(w in deb_norm for w in pers_keywords):
            cat_data["PERSONAL"].append(deb)
        else:
            cat_data["PROCESOS"].append(deb)

    for am in amenazas:
        am_norm = clean_text_for_ish(am)
        if any(w in am_norm for w in tech_keywords):
            cat_data["TECNOLOGÍA"].append(am)
        elif any(w in am_norm for w in pers_keywords):
            cat_data["PERSONAL"].append(am)
        else:
            cat_data["ENTORNO"].append(am)

    for cat in cat_data:
        if not cat_data[cat]:
            cat_data[cat] = ["Sin decesos o amenazas operativas"]
            
    pdf.set_line_width(0.7)
    for esp in espinas:
        # Dibujar espina principal
        pdf.set_draw_color(*esp["color"])
        pdf.line(esp["x_start"], esp["y_start"], esp["x_end"], esp["y_end"])
        
        # Etiqueta de la categoría
        pdf.set_font('Courier', 'B', 8)
        pdf.set_text_color(*esp["color"])
        if esp["y_end"] < spine_y:
            pdf.set_xy(esp["x_end"] - 15, esp["y_end"] - 4.5)
        else:
            pdf.set_xy(esp["x_end"] - 15, esp["y_end"] + 1.5)
        pdf.cell(30, 4, esp["nombre"], 0, 0, 'C')
        
        # Causas en espinas secundarias (hasta 6 para que quepa todo de forma completa)
        factors = cat_data.get(esp["nombre"], [])
        num_factors = len(factors)
        is_left = (esp["x_start"] < x_origin + 100)
        
        pdf.set_font('Courier', '', 5.5)
        pdf.set_text_color(220, 220, 220)
        
        for idx, fact in enumerate(factors[:6]):
            # Calcular posición fraccional distribuida a lo largo de la espina
            frac = 0.2 + (0.7 / max(1, num_factors - 1)) * idx if num_factors > 1 else 0.5
            fx = esp["x_start"] + (esp["x_end"] - esp["x_start"]) * frac
            fy = spine_y + (esp["y_end"] - spine_y) * frac
            
            # Puntero horizontal
            pdf.set_draw_color(*esp["color"])
            pdf.set_line_width(0.15)
            # Dibujar hacia la izquierda si es del lado izquierdo, o derecha
            if is_left:
                pdf.line(fx, fy, fx - 10, fy)
                txt_x = max(x_origin + 2, fx - 75)
                txt_w = (fx - 11) - txt_x
                pdf.set_xy(txt_x, fy - 1.5)
                max_chars = max(5, int(txt_w / 1.16))
                pdf.cell(txt_w, 3, clean_pdf_string(fact[:max_chars]), 0, 0, 'R')
            else:
                pdf.line(fx, fy, fx + 10, fy)
                txt_x = fx + 11
                max_x = x_origin + width - 40
                txt_w = max(5, max_x - txt_x)
                pdf.set_xy(txt_x, fy - 1.5)
                max_chars = max(5, int(txt_w / 1.16))
                pdf.cell(txt_w, 3, clean_pdf_string(fact[:max_chars]), 0, 0, 'L')
            
    # Borde
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.5)
    pdf.rect(x_origin, y_origin, width, height, 'D')

def draw_monte_carlo(pdf, x_origin, y_origin, size, resultados):
    # Fondo
    pdf.set_fill_color(2, 6, 23)
    pdf.rect(x_origin, y_origin, size, size, 'F')
    
    # Rejilla
    pdf.set_draw_color(20, 35, 75)
    pdf.set_line_width(0.15)
    divisions = 8
    step = size / divisions
    for i in range(1, divisions):
        pdf.line(x_origin, y_origin + i * step, x_origin + size, y_origin + i * step)
        pdf.line(x_origin + i * step, y_origin, x_origin + i * step, y_origin + size)
        
    # Ejes
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.4)
    pdf.line(x_origin, y_origin + size/2, x_origin + size, y_origin + size/2)
    pdf.line(x_origin + size/2, y_origin, x_origin + size/2, y_origin + size)
    
    # Nube de puntos (espectro de escenarios)
    pdf.set_fill_color(57, 255, 20)
    # Dibujar ~300 puntos para optimizar peso/velocidad del PDF
    for idx in range(0, len(resultados), 3):
        rx, ry = resultados[idx]
        px = x_origin + (rx + 50.0) / 100.0 * size
        py = y_origin + (50.0 - ry) / 100.0 * size
        
        # Clamp
        px = max(x_origin + 0.5, min(x_origin + size - 0.5, px))
        py = max(y_origin + 0.5, min(y_origin + size - 0.5, py))
        
        pdf.rect(px - 0.2, py - 0.2, 0.4, 0.4, 'F')
        
    # Borde
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.5)
    pdf.rect(x_origin, y_origin, size, size, 'D')

def draw_line_chart(pdf, x_origin, y_origin, width, height, hist):
    # Fondo
    pdf.set_fill_color(2, 6, 23)
    pdf.rect(x_origin, y_origin, width, height, 'F')
    
    # Rejilla horizontal e indicadores Y
    pdf.set_draw_color(20, 35, 75)
    pdf.set_line_width(0.15)
    for y_val in [-40, -20, 0, 20, 40]:
        py = y_origin + height/2 - (y_val / 100.0) * (height - 10)
        pdf.line(x_origin + 8, py, x_origin + width - 5, py)
        pdf.set_font('Courier', '', 5)
        pdf.set_text_color(100, 150, 200)
        pdf.set_xy(x_origin + 2, py - 1)
        pdf.cell(5, 2, f"{y_val}", 0, 0, 'R')
        
    # Rejilla vertical e indicadores X
    for t in range(0, 13, 2):
        px = x_origin + 8 + (t / 12.0) * (width - 15)
        pdf.line(px, y_origin + 4, px, y_origin + height - 5)
        pdf.set_font('Courier', '', 5)
        pdf.set_text_color(100, 150, 200)
        pdf.set_xy(px - 3, y_origin + height - 4.5)
        pdf.cell(6, 3, f"t={t}", 0, 0, 'C')
        
    # Ejes base
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.4)
    pdf.line(x_origin + 8, y_origin + 4, x_origin + 8, y_origin + height - 5)
    pdf.line(x_origin + 8, y_origin + height/2, x_origin + width - 5, y_origin + height/2)
    
    # Dibujo de curvas
    def get_coords(t_val, val):
        px = x_origin + 8 + (t_val / 12.0) * (width - 15)
        py = y_origin + height/2 - (val / 100.0) * (height - 10)
        px = max(x_origin + 8, min(x_origin + width - 5, px))
        py = max(y_origin + 4, min(y_origin + height - 5, py))
        return px, py
        
    # Curva Interno (X) - Celeste neón
    pdf.set_draw_color(0, 242, 255)
    pdf.set_line_width(0.7)
    for i in range(len(hist) - 1):
        x1, y1 = get_coords(hist[i][0], hist[i][1])
        x2, y2 = get_coords(hist[i+1][0], hist[i+1][1])
        pdf.line(x1, y1, x2, y2)
        
    # Curva Externo (Y) - Verde neón
    pdf.set_draw_color(57, 255, 20)
    for i in range(len(hist) - 1):
        x1, y1 = get_coords(hist[i][0], hist[i][2])
        x2, y2 = get_coords(hist[i+1][0], hist[i+1][2])
        pdf.line(x1, y1, x2, y2)
        
def estimate_strategy_height(text, font_size, line_height):
    parsed = parse_came_text(text)
    
    # Calculate characters per line dynamically based on font size and column width
    # Column width is 125mm for paragraphs. Width in points is 125 * 2.8346 = 354.3 points.
    # Courier char width is font_size * 0.6 points.
    # Max chars per line = 354.3 / (font_size * 0.6) = 590.5 / font_size.
    # We use a conservative factor of 530 to account for word wrapping on boundaries.
    chars_per_line_p = max(20, int(530.0 / font_size))
    
    # Recommendations column width is 119mm. Width in points is 119 * 2.8346 = 337.3 points.
    # Max chars per line = 337.3 / (font_size * 0.6) = 562.2 / font_size.
    # We use a conservative factor of 500.
    chars_per_line_rec = max(20, int(500.0 / font_size))

    if not parsed or (not parsed["part1_paragraphs"] and not parsed["part2_paragraphs"] and not parsed["recs"]):
        text_clean = "\n".join([line.strip() for line in text.split('\n') if line.strip()])
        lines = sum(max(1, (len(line) + chars_per_line_p - 1) // chars_per_line_p) for line in text_clean.split('\n'))
        return lines * line_height
        
    h = 0.0
    if parsed["part1_paragraphs"]:
        h += (line_height + 0.5) # Header
        for idx, p in enumerate(parsed["part1_paragraphs"]):
            p_len = len(p) + (5 if idx > 0 else 0)
            lines = max(1, (p_len + chars_per_line_p - 1) // chars_per_line_p)
            h += lines * line_height
        h += 1.0 # ln(1.0)
    if parsed["part2_paragraphs"]:
        h += (line_height + 0.5) # Header
        for idx, p in enumerate(parsed["part2_paragraphs"]):
            p_len = len(p) + (5 if idx > 0 else 0)
            lines = max(1, (p_len + chars_per_line_p - 1) // chars_per_line_p)
            h += lines * line_height
        h += 1.0 # ln(1.0)
    if parsed["recs"]:
        h += (line_height + 0.5) # Header
        for rec in parsed["recs"]:
            lines = max(1, (len(rec) + chars_per_line_rec - 1) // chars_per_line_rec)
            h += lines * line_height
    return h

def estimate_ia_report_height(sections, texto_limpio, font_size, line_height, spacing_paragraph):
    if not sections:
        lines = sum(max(1, (len(line) + 145 - 1) // 145) for line in texto_limpio.split('\n'))
        return lines * line_height
        
    h = 0.0
    for title in ["SITUACIÓN GENERAL", "AMENAZAS", "RIESGOS", "LÍNEAS DE ACCIÓN"]:
        content = sections.get(title, "").strip()
        if not content: continue
        h += (line_height + 1.0) # Title
        
        if title == "SITUACIÓN GENERAL":
            paragraphs = [line.strip() for line in content.split('\n') if line.strip()]
            for p in paragraphs:
                cleaned_p = re.sub(r'^\s*(?:\d+[\.\-\s\)]+|[\*\-\+])\s*', '', p).strip()
                if cleaned_p:
                    lines = max(1, (len(cleaned_p) + 145 - 1) // 145)
                    h += lines * line_height
                    h += spacing_paragraph
            h += 0.5
        else:
            content_lines = [line.strip() for line in content.split('\n') if line.strip()]
            for line in content_lines:
                match = re.match(r'^(\d+\.\s*)(.*)', line)
                text_part = match.group(2) if match else line
                lines = max(1, (len(text_part) + 140 - 1) // 140)
                h += lines * line_height
            h += spacing_paragraph
    return h

def crear_pdf_final(foda_dict, texto_ia, x, y, perfil="Analista", tipo_ana="General", fecha_i=None, fecha_t=None, prob_exito=50.0, bitacora=None, acciones=None, votos=None, total_votantes=10, came_estrategias=None, stress_int=0.0, stress_ext=0.0, progress_cb=None):
    if progress_cb: progress_cb(0.10, "Cargando componentes tácticos y normalizando matrices...")
    # Reconstrucción de los DataFrames desde foda_dict
    df_f = pd.DataFrame(foda_dict.get("F", []))
    df_d = pd.DataFrame(foda_dict.get("D", []))
    df_o = pd.DataFrame(foda_dict.get("O", []))
    df_a = pd.DataFrame(foda_dict.get("A", []))
    
    # Asegurar que tengan las columnas requeridas si están vacíos
    for df_item in [df_f, df_d, df_o, df_a]:
        if "Factor" not in df_item.columns:
            df_item["Factor"] = []
        if "Peso" not in df_item.columns:
            df_item["Peso"] = []
        if "Calificación" not in df_item.columns:
            df_item["Calificación"] = []
    
    # Usar fpdf2 con Carta Horizontal (letter: 279.4 x 215.9 mm)
    pdf = TacticalPDF(orientation='L', unit='mm', format='letter')
    pdf.set_auto_page_break(auto=False)
    
    # ---------------------------------------------------------
    # PAGINA 1: MATRICES PONDERADAS (Pestaña 1)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.20, "Generando Hoja 1: Matrices de Evaluación Ponderada...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 1: MATRICES DE EVALUACIÓN PONDERADA (FODA)", 0, 1)
    pdf.ln(3)
    
    f_total = sum(item.get('Peso', 0) * item.get('Calificación', 0) for item in foda_dict.get("F", []))
    d_total = sum(item.get('Peso', 0) * item.get('Calificación', 0) for item in foda_dict.get("D", []))
    o_total = sum(item.get('Peso', 0) * item.get('Calificación', 0) for item in foda_dict.get("O", []))
    a_total = sum(item.get('Peso', 0) * item.get('Calificación', 0) for item in foda_dict.get("A", []))
    
    sum_mefi = sum(item.get('Peso', 0) for item in foda_dict.get("F", [])) + sum(item.get('Peso', 0) for item in foda_dict.get("D", []))
    sum_mefe = sum(item.get('Peso', 0) for item in foda_dict.get("O", [])) + sum(item.get('Peso', 0) for item in foda_dict.get("A", []))
    
    pdf.set_font("Courier", 'B', 10)
    pdf.set_text_color(220, 220, 220)
    pdf.cell(0, 6, f"PONDERACIÓN MEFI ACTIVA (SUMA PESOS: {sum_mefi:.2f}/1.00)  |  PONDERACIÓN MEFE ACTIVA (SUMA PESOS: {sum_mefe:.2f}/1.00)", 0, 1)
    pdf.cell(0, 6, f"TOTAL PONDERADO MEFI (F - D): {f_total - d_total:+.2f}  |  TOTAL PONDERADO MEFE (O - A): {o_total - a_total:+.2f}", 0, 1)
    pdf.ln(4)
    
    def dibujar_tabla_columna(x_offset, y_start, titulo, lista):
        pdf.set_xy(x_offset, y_start)
        pdf.set_font("Courier", 'B', 10)
        pdf.set_text_color(0, 242, 255)
        pdf.cell(120, 6, clean_pdf_string(titulo), 0, 1)
        
        pdf.set_x(x_offset)
        pdf.set_fill_color(20, 30, 55)
        pdf.set_font("Courier", 'B', 8)
        pdf.set_text_color(0, 242, 255)
        pdf.cell(76, 5, "Factor", 1, 0, 'C', True)
        pdf.cell(22, 5, "Peso", 1, 0, 'C', True)
        pdf.cell(22, 5, "Calif.", 1, 1, 'C', True)
        
        pdf.set_font("Courier", '', 8)
        pdf.set_text_color(220, 220, 220)
        
        if not lista:
            pdf.set_x(x_offset)
            pdf.cell(120, 5, "  (Sin factores operativos registrados)", 1, 1)
            return
            
        for item in lista[:8]:
            pdf.set_x(x_offset)
            factor = clean_pdf_string(item.get('Factor', '')[:38])
            peso = f"{item.get('Peso', 0):.3f}"
            calif = f"{item.get('Calificación', 0):.1f}"
            pdf.cell(76, 5, factor, 1)
            pdf.cell(22, 5, peso, 1, 0, 'R')
            pdf.cell(22, 5, calif, 1, 1, 'R')
            
    dibujar_tabla_columna(10, 44, "FORTALEZAS F (MEFI - Interno)", foda_dict.get("F", []))
    dibujar_tabla_columna(10, 114, "DEBILIDADES D (MEFI - Interno)", foda_dict.get("D", []))
    
    dibujar_tabla_columna(148, 44, "OPORTUNIDADES O (MEFE - Externo)", foda_dict.get("O", []))
    dibujar_tabla_columna(148, 114, "AMENAZAS A (MEFE - Externo)", foda_dict.get("A", []))
    
    # ---------------------------------------------------------
    # PAGINA 2: DIAGNÓSTICO ESTRATÉGICO (Pestaña 2)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.35, "Generando Hoja 2: Diagnóstico Estratégico y Posicionamiento Vectorial...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 2: DIAGNÓSTICO ESTRATÉGICO Y POSICIONAMIENTO VECTORIAL", 0, 1)
    pdf.ln(3)
    
    pdf.set_fill_color(5, 12, 36)
    pdf.set_draw_color(0, 242, 255)
    pdf.rect(10, 32, 80, 150, 'DF')
    
    pdf.set_xy(13, 38)
    pdf.set_font("Courier", 'B', 11)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 6, "SITUACIÓN OPERACIONAL S5", 0, 1)
    pdf.ln(3)
    
    pdf.set_font("Courier", '', 9)
    pdf.set_text_color(220, 220, 220)
    
    fi_str = fecha_i.strftime("%Y-%m-%d") if hasattr(fecha_i, 'strftime') else str(fecha_i or datetime.today().date())
    ft_str = fecha_t.strftime("%Y-%m-%d") if hasattr(fecha_t, 'strftime') else str(fecha_t or datetime.today().date())
    
    pdf.set_x(13)
    pdf.cell(0, 6, f"PERFIL MISIÓN: {clean_pdf_string(perfil).upper()}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 6, f"CATEGORÍA    : {clean_pdf_string(tipo_ana).upper()}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 6, f"INICIO       : {fi_str}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 6, f"FIN          : {ft_str}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 6, f"EMISIÓN      : {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.ln(4)
    
    pdf.set_x(13)
    pdf.set_font("Courier", 'B', 10)
    pdf.set_text_color(57, 255, 20)
    pdf.cell(0, 7, f">> VECTOR: X={x:+.2f} / Y={y:+.2f}", 0, 1)
    
    scores_obj = {"interno": x/10.0, "externo": y/10.0, "F": f_total, "D": d_total, "O": o_total, "A": a_total}
    classification_str = clasificacion(scores_obj)
    estado = classification_str.replace("ESTADO: ", "")
    
    directiva = decidir(scores_obj, prob_exito)
    directiva_clean = directiva.replace("DIRECTIVA ALFA: ", "").replace("DIRECTIVA BRAVO: ", "").replace("DIRECTIVA CHARLIE: ", "").replace("DIRECTIVA DELTA: ", "")
    
    if x > 0 and y > 0:
        color_alert = (57, 255, 20)
    elif x < 0 and y > 0:
        color_alert = (255, 170, 0)
    elif x > 0 and y < 0:
        color_alert = (0, 242, 255)
    else:
        color_alert = (255, 0, 85)
        
    pdf.set_x(13)
    pdf.set_font("Courier", 'B', 9)
    pdf.set_text_color(*color_alert)
    pdf.multi_cell(74, 5.5, f">> ESTADO:\n{estado}", 0, 'L')
    pdf.ln(2)
    
    pdf.set_x(13)
    pdf.set_text_color(220, 220, 220)
    pdf.multi_cell(74, 5, f">> DIRECTIVA:\n{directiva_clean}", 0, 'L')
    pdf.ln(3)
    
    pdf.set_x(13)
    pdf.set_font("Courier", 'B', 8.5)
    if a_total > o_total:
        pdf.set_text_color(255, 0, 85)
        pdf.cell(0, 5, "! RIESGO: ENTORNO HOSTIL (A > O)", 0, 1)
    if d_total > f_total:
        pdf.set_text_color(255, 170, 0)
        pdf.cell(0, 5, "! AVISO: DEBILIDAD INTERNA (D > F)", 0, 1)
    if f_total > d_total and o_total > a_total:
        pdf.set_text_color(57, 255, 20)
        pdf.cell(0, 5, "* OPTIMO: SUPERIORIDAD CONFIRMADA", 0, 1)
        
    draw_cartesian_plane(pdf, x_origin=95, y_origin=32, size=90, x_val=x, y_val=y)
    
    draw_radar_chart(pdf, x_center=232, y_center=72, radius=32, scores=scores_obj)
    draw_bar_chart(pdf, x_origin=195, y_origin=116, width=74, height=66, scores=scores_obj)
    
    # ---------------------------------------------------------
    # PAGINA 3: ANÁLISIS CAUSA-EFECTO (Pestaña 3)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.50, "Generando Hoja 3: Diagrama de Causa-Efecto (Ishikawa)...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 3: DIAGRAMA DE CAUSA-EFECTO (ISHIKAWA)", 0, 1)
    pdf.ln(3)
    

        
    draw_ishikawa(pdf, x_origin=15, y_origin=38, width=250, height=145, df_d=df_d, df_a=df_a, estado_actual=classification_str)
    
    # ---------------------------------------------------------
    # PAGINA 4: FORMULACIÓN ESTRATÉGICA CAME (Pestaña 4)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.65, "Generando Hoja 4: Formulación CAME y Posturas...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 4: FORMULACIÓN ESTRATÉGICA CAME Y POSTURAS", 0, 1)
    pdf.ln(2)
    
    pdf.set_fill_color(20, 30, 55)
    pdf.set_font("Courier", 'B', 8.5)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(45, 5, "Factor FODA", 1, 0, 'C', True)
    pdf.cell(25, 5, "Origen", 1, 0, 'C', True)
    pdf.cell(30, 5, "Acción CAME", 1, 0, 'C', True)
    pdf.cell(159, 5, "Enfoque Estratégico", 1, 1, 'C', True)
    
    pdf.set_font("Courier", '', 8)
    pdf.set_text_color(220, 220, 220)
    
    pdf.set_text_color(255, 170, 0)
    pdf.cell(45, 4.5, "Debilidades (D)", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(25, 4.5, "Interno", 1, 0, 'C')
    pdf.set_text_color(255, 170, 0)
    pdf.cell(30, 4.5, "CORREGIR", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(159, 4.5, "Corregir debilidades internas de la institución y brechas operativas.", 1, 1, 'L')
    
    pdf.set_text_color(255, 0, 85)
    pdf.cell(45, 4.5, "Amenazas (A)", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(25, 4.5, "Externo", 1, 0, 'C')
    pdf.set_text_color(255, 0, 85)
    pdf.cell(30, 4.5, "AFRONTAR", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(159, 4.5, "Afrontar riesgos externos del entorno para resistir hostilidad.", 1, 1, 'L')
    
    pdf.set_text_color(57, 255, 20)
    pdf.cell(45, 4.5, "Fortalezas (F)", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(25, 4.5, "Interno", 1, 0, 'C')
    pdf.set_text_color(57, 255, 20)
    pdf.cell(30, 4.5, "MANTENER", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(159, 4.5, "Mantener fortalezas internas y consolidar ventajas competitivas.", 1, 1, 'L')
    
    pdf.set_text_color(0, 242, 255)
    pdf.cell(45, 4.5, "Oportunidades (O)", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(25, 4.5, "Externo", 1, 0, 'C')
    pdf.set_text_color(0, 242, 255)
    pdf.cell(30, 4.5, "EXPLOTAR", 1, 0, 'C')
    pdf.set_text_color(220, 220, 220)
    pdf.cell(159, 4.5, "Explotar oportunidades externas nacional o internacional.", 1, 1, 'L')
    
    pdf.ln(5)
    
    came_est = came_estrategias or {}
    text_fo = came_est.get("A. Estrategia Ofensiva (F + O)", "") or "(Estrategia no formulada en esta sesión)"
    text_fa = came_est.get("C. Estrategia Defensiva (F + A)", "") or "(Estrategia no formulada en esta sesión)"
    text_da = came_est.get("B. Estrategia de Supervivencia (D + A)", "") or "(Estrategia no formulada en esta sesión)"
    text_do = came_est.get("D. Estrategia de Reorientación (D + O)", "") or "(Estrategia no formulada en esta sesión)"
    
    font_options = [
        (8.0, 3.6),
        (7.5, 3.2),
        (7.0, 3.0),
        (6.5, 2.7),
        (6.0, 2.5),
        (5.5, 2.3),
        (5.0, 2.1)
    ]
    
    font_size_came = 8.0
    line_height_came = 3.6
    y_inicio_bottom = 100.0
    
    for f_sz, l_ht in font_options:
        h_fo = estimate_strategy_height(text_fo, f_sz, l_ht)
        h_da = estimate_strategy_height(text_da, f_sz, l_ht)
        h_fa = estimate_strategy_height(text_fa, f_sz, l_ht)
        h_do = estimate_strategy_height(text_do, f_sz, l_ht)
        
        y_bottom = max(66 + h_fo, 66 + h_da) + 5
        y_temp_bottom = max(y_bottom, 100.0)
        max_end_y = max(y_temp_bottom + 6 + h_fa, y_temp_bottom + 6 + h_do)
        
        if max_end_y <= 200.0 or f_sz == 5.0:
            font_size_came = f_sz
            line_height_came = l_ht
            y_inicio_bottom = y_temp_bottom
            break
            
    # FO (Ofensiva)
    pdf.set_xy(10, 60)
    pdf.set_font("Courier", 'B', font_size_came + 2.5)
    pdf.set_text_color(57, 255, 20)
    pdf.cell(125, 5, ">> ESTRATEGIA OFENSIVA (FO) - MANTENER + EXPLOTAR", 0, 1)
    render_came_strategy_pdf(pdf, 10, 66, 125, text_fo, font_size_came, line_height_came, (57, 255, 20))
    
    # FA (Defensiva)
    pdf.set_xy(10, y_inicio_bottom)
    pdf.set_font("Courier", 'B', font_size_came + 2.5)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(125, 5, ">> ESTRATEGIA DEFENSIVA (FA) - MANTENER + AFRONTAR", 0, 1)
    render_came_strategy_pdf(pdf, 10, y_inicio_bottom + 6, 125, text_fa, font_size_came, line_height_came, (0, 242, 255))
    
    # DA (Supervivencia)
    pdf.set_xy(145, 60)
    pdf.set_font("Courier", 'B', font_size_came + 2.5)
    pdf.set_text_color(255, 0, 85)
    pdf.cell(125, 5, ">> ESTRATEGIA DE SUPERVIVENCIA (DA) - CORREGIR + AFRONTAR", 0, 1)
    render_came_strategy_pdf(pdf, 145, 66, 125, text_da, font_size_came, line_height_came, (255, 0, 85))
    
    # DO (Reorientación)
    pdf.set_xy(145, y_inicio_bottom)
    pdf.set_font("Courier", 'B', font_size_came + 2.5)
    pdf.set_text_color(255, 170, 0)
    pdf.cell(125, 5, ">> ESTRATEGIA DE REORIENTACIÓN (DO) - CORREGIR + EXPLOTAR", 0, 1)
    render_came_strategy_pdf(pdf, 145, y_inicio_bottom + 6, 125, text_do, font_size_came, line_height_came, (255, 170, 0))
    
    # ---------------------------------------------------------
    # PAGINA 5: ANÁLISIS DE RIESGO & ESTRÉS (Pestaña 5)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.80, "Generando Hoja 5: Análisis de Riesgo Monte Carlo y Estrés...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 5: ANÁLISIS DE RIESGO ESTOCÁSTICO (MONTE CARLO) & ESTRÉS", 0, 1)
    pdf.ln(3)
    
    pdf.set_fill_color(5, 12, 36)
    pdf.set_draw_color(0, 242, 255)
    pdf.rect(10, 32, 82, 150, 'DF')
    
    pdf.set_xy(13, 38)
    pdf.set_font("Courier", 'B', 11)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 6, "MÉTRICAS DE PRUEBA DE ESTRÉS", 0, 1)
    pdf.ln(3)
    
    pdf.set_font("Courier", '', 8.0)
    pdf.set_text_color(220, 220, 220)
    
    resultados_mc = simulacion_montecarlo(df_f, df_d, df_o, df_a, stress_int, stress_ext)
    hist_omega = simular_periodos(df_f, df_d, df_o, df_a, stress_int, stress_ext, T=13)
    
    pdf.set_x(13)
    pdf.cell(0, 5, f"PROB. ÉXITO        : {prob_exito:.2f}%", 0, 1)
    
    risk_text = "BAJO RIESGO" if prob_exito > 70 else ("RIESGO MODERADO" if prob_exito > 40 else "ALTO RIESGO")
    pdf.set_x(13)
    pdf.cell(0, 5, f"NIVEL DE RIESGO    : {risk_text}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 5, f"ESTRÉS INTERNO (X) : {stress_int:+.1f}", 0, 1)
    pdf.set_x(13)
    pdf.cell(0, 5, f"ESTRÉS EXTERNO (Y) : {stress_ext:+.1f}", 0, 1)
    pdf.ln(3)
    
    try:
        (mejor_f, mejor_d, mejor_o, mejor_a), score_opt = optimizar(df_f, df_d, df_o, df_a)
        pdf.set_x(13)
        pdf.set_font("Courier", 'B', 8.0)
        pdf.set_text_color(57, 255, 20)
        pdf.cell(0, 5, f"MAX BALANCE ÓPTIMO : {score_opt:.3f}", 0, 1)
    except Exception:
        pass
        
    pdf.ln(4)
    pdf.set_x(13)
    pdf.set_font("Courier", 'B', 9.5)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 6, "PLAN DE RESPUESTA DIRECTIVO:", 0, 1)
    pdf.ln(2)
    
    pdf.set_font("Courier", '', 8)
    pdf.set_text_color(220, 220, 220)
    if prob_exito > 70:
        contingencia = ["* Monitorear indicadores regularmente.", "* Continuar con directivas ordinarias."]
    elif prob_exito > 40:
        contingencia = ["* Activar protocolos preventivos.", "* Diversificar canales y capacidades.", "* Reforzar enlaces tecnologicos."]
    else:
        contingencia = ["* ALERTA: Activar planes de contingencia.", "* Restringir ejecucion de directivas.", "* Iniciar auditoria de ciberdefensa."]
        
    for item in contingencia:
        pdf.set_x(13)
        pdf.cell(0, 5, item, 0, 1)
        
    draw_monte_carlo(pdf, x_origin=95, y_origin=32, size=82, resultados=resultados_mc)
    pdf.set_font('Courier', 'B', 8.5)
    pdf.set_text_color(0, 242, 255)
    pdf.set_xy(95, 116)
    pdf.cell(82, 5, "SIM // DISPERSIÓN DE ESCENARIOS MC", 0, 0, 'C')
    
    draw_line_chart(pdf, x_origin=185, y_origin=32, width=84, height=82, hist=hist_omega)
    pdf.set_xy(185, 116)
    pdf.cell(84, 5, "OMEGA // PROYECCIÓN DE EVOLUCIÓN", 0, 0, 'C')
    
    pdf.set_xy(95, 126)
    pdf.set_font("Courier", 'B', 8.5)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 6, "TABLA HISTÓRICA PROYECTADA (MUESTRA CLAVE)", 0, 1)
    
    pdf.set_fill_color(20, 30, 55)
    pdf.set_font("Courier", 'B', 8)
    pdf.set_xy(95, 133)
    pdf.cell(30, 5.5, "Período (t)", 1, 0, 'C', True)
    pdf.cell(72, 5.5, "Situación Interna X (Mod)", 1, 0, 'C', True)
    pdf.cell(72, 5.5, "Situación Externa Y (Mod)", 1, 1, 'C', True)
    
    pdf.set_font("Courier", '', 8)
    pdf.set_text_color(210, 210, 210)
    for p in [0, 2, 4, 6, 8, 10, 12]:
        row_data = hist_omega[p]
        pdf.set_x(95)
        pdf.cell(30, 5, f"t = {int(row_data[0])}", 1, 0, 'C')
        pdf.cell(72, 5, f"{row_data[1]:+.2f}", 1, 0, 'C')
        pdf.cell(72, 5, f"{row_data[2]:+.2f}", 1, 1, 'C')
        
    # ---------------------------------------------------------
    # PAGINA 6: INFORME IA & EXPORTACIÓN (Pestaña 6)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.90, "Generando Hoja 6: Informe de Inteligencia Estratégico (IA)...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 6: INFORME DE INTELIGENCIA ESTRATÉGICO (MOTOR IA OLLAMA)", 0, 1)
    pdf.ln(2)
    
    texto_limpio = re.sub(
        r'(SITUACI[OÓ]N\s+GENERAL[:\s]*)\n+\s*(?:\d+[\.\-\s\)]+|[\*\-\+])\s*',
        r'\1\n',
        texto_ia,
        flags=re.IGNORECASE
    )
    texto_limpio = texto_limpio.replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
    texto_limpio = clean_pdf_string(texto_limpio)
    
    headers_pdf = [
        ("SITUACIÓN GENERAL", [r"situaci[oó]n\s+general"]),
        ("AMENAZAS", [r"amenazas"]),
        ("RIESGOS", [r"riesgos"]),
        ("LÍNEAS DE ACCIÓN", [r"l[ií]neas\s+de\s+acci[oó]n", r"lineas\s+de\s+accion"])
    ]
    
    section_indices = []
    for title, regexes in headers_pdf:
        for regex in regexes:
            pattern = r"(?:^|\n)[^a-zA-Z0-9\n]*" + regex + r"[:#\*\-\s]*"
            match = re.search(pattern, texto_limpio, re.IGNORECASE)
            if match:
                section_indices.append((match.start(), match.end(), title))
                break
                
    section_indices.sort(key=lambda x: x[0])
    
    sections = {}
    for i in range(len(section_indices)):
        start_idx, end_idx, title = section_indices[i]
        next_start = section_indices[i+1][0] if i + 1 < len(section_indices) else len(texto_limpio)
        sections[title] = texto_limpio[end_idx:next_start].strip()
        
    font_options_ia = [
        (8.5, 4.0, 1.5),
        (8.0, 3.6, 1.3),
        (7.5, 3.4, 1.2),
        (7.0, 3.1, 1.1),
        (6.5, 2.8, 1.0),
        (6.0, 2.5, 0.8),
        (5.5, 2.2, 0.7),
        (5.0, 2.0, 0.6)
    ]
    
    font_size_ia = 8.5
    line_height_ia = 4.0
    spacing_paragraph_ia = 1.5
    
    for f_sz, l_ht, sp_pg in font_options_ia:
        est_h = estimate_ia_report_height(sections, texto_limpio, f_sz, l_ht, sp_pg)
        if est_h <= 165.0 or f_sz == 5.0:
            font_size_ia = f_sz
            line_height_ia = l_ht
            spacing_paragraph_ia = sp_pg
            break
        
    if not sections:
        pdf.set_font("Courier", '', font_size_ia)
        pdf.set_text_color(220, 220, 220)
        pdf.multi_cell(0, line_height_ia, texto_limpio, align='J')
    else:
        for title in ["SITUACIÓN GENERAL", "AMENAZAS", "RIESGOS", "LÍNEAS DE ACCIÓN"]:
            content = sections.get(title, "").strip()
            if not content: continue
                
            pdf.set_font("Courier", 'B', font_size_ia + 1.5)
            
            if title == "SITUACIÓN GENERAL":
                pdf.set_text_color(0, 242, 255)
            elif title == "AMENAZAS":
                pdf.set_text_color(255, 170, 0)
            elif title == "RIESGOS":
                pdf.set_text_color(255, 0, 85)
            else:
                pdf.set_text_color(57, 255, 20)
                
            pdf.cell(0, line_height_ia + 1.0, f">> {title}", 0, 1)
            pdf.set_font("Courier", '', font_size_ia)
            pdf.set_text_color(220, 220, 220)
            
            if title == "SITUACIÓN GENERAL":
                paragraphs = [line.strip() for line in content.split('\n') if line.strip()]
                for idx, p in enumerate(paragraphs):
                    cleaned_p = re.sub(r'^\s*(?:\d+[\.\-\s\)]+|[\*\-\+])\s*', '', p).strip()
                    if cleaned_p:
                        indent = "     " if idx > 0 else ""
                        pdf.multi_cell(0, line_height_ia, indent + cleaned_p, align='J')
                        pdf.ln(spacing_paragraph_ia)
                pdf.ln(0.5)
            else:
                content_lines = [line.strip() for line in content.split('\n') if line.strip()]
                for line in content_lines:
                    match = re.match(r'^(\d+\.\s*)(.*)', line)
                    if match:
                        num_part = match.group(1)
                        text_part = match.group(2)
                    else:
                        num_part = ""
                        text_part = line
                    
                    current_y = pdf.get_y()
                    old_l_margin = pdf.l_margin
                    
                    if num_part:
                        pdf.set_xy(old_l_margin, current_y)
                        pdf.set_font("Courier", 'B', font_size_ia)
                        pdf.set_text_color(255, 255, 255)
                        pdf.write(line_height_ia, num_part)
                    
                    pdf.set_left_margin(old_l_margin + 8)
                    pdf.set_xy(old_l_margin + 8, current_y)
                    
                    pdf.set_font("Courier", '', font_size_ia)
                    pdf.set_text_color(220, 220, 220)
                    pdf.multi_cell(0, line_height_ia, text_part, align='J')
                    pdf.set_left_margin(old_l_margin)
                pdf.ln(spacing_paragraph_ia)
                
    # ---------------------------------------------------------
    # PAGINA 7: MANDO Y BITÁCORA (Pestaña 7)
    # ---------------------------------------------------------
    if progress_cb: progress_cb(0.98, "Generando Hoja 7: Mando Compartido y Registro Audit...")
    pdf.add_page()
    pdf.set_y(22)
    pdf.set_font("Courier", 'B', 14)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(0, 8, "PESTAÑA 7: MANDO COMPARTIDO Y BITÁCORA DE OPERACIONES S5", 0, 1)
    pdf.ln(3)
    
    pdf.set_xy(10, 36)
    pdf.set_font("Courier", 'B', 11)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(130, 6, ">> MANDO COMPARTIDO / VOTACIÓN ESTRATÉGICA CAME", 0, 1)
    pdf.ln(2)
    
    pdf.set_font("Courier", '', 9.5)
    pdf.set_text_color(220, 220, 220)
    votos_map = votos or {"FO": 0, "DO": 0, "FA": 0, "DA": 0}
    total_v = total_votantes or 10
    
    def calcular_consenso_local(v, t):
        if t <= 0: return "CONFIGURACIÓN DE VOTANTES INVÁLIDA"
        ganador = max(v, key=v.get)
        votos_ganador = v[ganador]
        if votos_ganador == 0: return "SIN VOTACIÓN ACTIVA"
        porcentaje = (votos_ganador / t) * 100
        if porcentaje > 60:
            return f"CONSENSO DIRECTIVA: {ganador} ({porcentaje:.1f}%)"
        else:
            return f"SIN CONSENSO: {ganador} CON {porcentaje:.1f}% (REQUERIDO > 60%)"
            
    consenso_str = calcular_consenso_local(votos_map, total_v)
    pdf.set_x(10)
    pdf.cell(130, 5, f"VOTANTES HABILITADOS: {total_v}", 0, 1)
    pdf.set_x(10)
    pdf.cell(130, 5, f"ESTADO DE CONSENSO  : {consenso_str}", 0, 1)
    pdf.ln(4)
    
    pdf.set_x(10)
    pdf.set_fill_color(20, 30, 55)
    pdf.set_font("Courier", 'B', 9)
    pdf.cell(35, 5, "Estrategia", 1, 0, 'C', True)
    pdf.cell(35, 5, "Votos", 1, 0, 'C', True)
    pdf.cell(40, 5, "Porcentaje (%)", 1, 1, 'C', True)
    
    pdf.set_font("Courier", '', 9)
    for opt in ["FO", "DO", "FA", "DA"]:
        pdf.set_x(10)
        v_opt = votos_map.get(opt, 0)
        pct = (v_opt / total_v) * 100
        pdf.cell(35, 5.5, f"ESTRATEGIA {opt}", 1, 0, 'C')
        pdf.cell(35, 5.5, f"{v_opt}", 1, 0, 'C')
        pdf.cell(40, 5.5, f"{pct:.1f}%", 1, 1, 'C')
        
    pdf.set_xy(145, 36)
    pdf.set_font("Courier", 'B', 11)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(120, 6, ">> PLAN DE ACCIÓN DIRECTIVO & DIRECTIVAS DE CONTROL", 0, 1)
    pdf.ln(2)
    
    pdf.set_font("Courier", '', 8.5)
    pdf.set_text_color(220, 220, 220)
    acciones_list = acciones or []
    
    pdf.set_x(145)
    if not acciones_list:
        pdf.cell(120, 5, "  (Sin acciones directivas activas en este turno)", 0, 1)
    else:
        for idx, a in enumerate(acciones_list[:5]):
            pdf.set_x(145)
            estado_acc = "[OK]" if a.get("estado", "") == "Completado" else "[PENDIENTE]"
            desc_acc = clean_pdf_string(a.get("accion", "")[:45])
            pdf.cell(120, 5, f"  {idx+1}. {estado_acc} {desc_acc}", 0, 1)
            
    pdf.set_xy(145, 85)
    pdf.set_font("Courier", 'B', 11)
    pdf.set_text_color(0, 242, 255)
    pdf.cell(120, 6, ">> AUDIT LOG / BITÁCORA DEL TURNO INMUTABLE", 0, 1)
    pdf.ln(2)
    
    pdf.set_font("Courier", '', 8)
    pdf.set_text_color(200, 200, 200)
    log_entries = bitacora or []
    if not log_entries:
        pdf.set_x(145)
        pdf.cell(120, 5, "  (Sin eventos registrados en la bitácora)", 0, 1)
    else:
        for log in log_entries[-8:]:
            pdf.set_x(145)
            ts = log.get('hora', '')
            ev = log.get('evento', '')
            pdf.cell(120, 4.5, f"  [{ts}] {clean_pdf_string(ev[:60])}", 0, 1)
            
    return bytes(pdf.output())