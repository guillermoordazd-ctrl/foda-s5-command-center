"""
FODA S5 - Launcher de Sistema Multiplataforma
Este script verifica e instala dependencias de requirements.txt de forma optimizada,
inicia Ollama local en segundo plano de manera asíncrona sin bloquear la interfaz,
y lanza el servidor Streamlit al instante.
"""

import os
import sys
import subprocess
import time
import threading

def log_tactical(msg):
    print(f"[SYS] {msg}")

def check_and_install_requirements():
    log_tactical("Verificando dependencias de Python...")
    try:
        # Intento rápido de importar dependencias clave para evitar la ejecución lenta de pip
        import streamlit
        import pandas
        import numpy
        import plotly
        import fpdf
        import requests
        import openpyxl
        log_tactical("[OK] Todas las dependencias de Python ya están instaladas y disponibles.")
    except ImportError:
        log_tactical("[AVISO] Faltan dependencias de Python. Instalando desde requirements.txt...")
        try:
            # Ejecutar pip install de forma silenciosa para asegurar que todas las librerías estén instaladas
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", "requirements.txt"])
            log_tactical("[OK] Dependencias de requirements.txt instaladas correctamente.")
        except Exception as e:
            log_tactical(f"[ERROR] No se pudieron instalar las dependencias de requirements.txt. Detalle: {e}")

def download_and_install_ollama_windows():
    log_tactical("[AVISO] Ollama no está instalado. Descargando el instalador oficial de Ollama para Windows...")
    installer_path = os.path.join(os.getcwd(), "OllamaSetup.exe")
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://ollama.com/download/OllamaSetup.exe",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response, open(installer_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        log_tactical("[OK] Descarga completa. Iniciando instalador silencioso en Windows (esto puede tomar un minuto)...")
        subprocess.run([installer_path, "/silent"], shell=True, check=True)
        log_tactical("[OK] Instalador ejecutado. Limpiando archivos temporales...")
        if os.path.exists(installer_path):
            os.remove(installer_path)
        return True
    except Exception as e:
        log_tactical(f"[ERROR] No se pudo descargar o instalar Ollama automáticamente: {e}")
        log_tactical("Por favor, descargue e instale Ollama manualmente desde https://ollama.com")
        return False

def create_windows_shortcut():
    if not sys.platform.startswith("win"):
        return
    
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop_path, "FODA S5 Command Center.lnk")
    
    log_tactical("Configurando acceso directo en el Escritorio de Windows...")
    
    python_exe = sys.executable
    if python_exe.lower().endswith("python.exe"):
        pythonw_candidate = python_exe[:-10] + "pythonw.exe"
        if os.path.exists(pythonw_candidate):
            python_exe = pythonw_candidate
    elif python_exe.lower().endswith("python"):
        pythonw_candidate = python_exe + "w"
        if os.path.exists(pythonw_candidate):
            python_exe = pythonw_candidate

    launcher_script = os.path.abspath(__file__)
    work_dir = os.path.dirname(launcher_script)
    icon_path = os.path.join(work_dir, "my_foda_s5.ico")
    
    ps_command = f"""
    $WshShell = New-Object -ComObject WScript.Shell;
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}');
    $Shortcut.TargetPath = '{python_exe}';
    $Shortcut.Arguments = '"{launcher_script}"';
    $Shortcut.WorkingDirectory = '{work_dir}';
    if (Test-Path '{icon_path}') {{
        $Shortcut.IconLocation = '{icon_path}';
    }}
    $Shortcut.Save();
    """
    
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        log_tactical("[OK] Acceso directo 'FODA S5 Command Center' creado en el Escritorio.")
    except Exception as e:
        log_tactical(f"[AVISO] No se pudo crear el acceso directo en el escritorio. Detalle: {e}")

def start_ollama_service():
    log_tactical("Verificando si el servicio de Ollama está activo...")
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=1.5)
        if resp.status_code == 200:
            log_tactical("[OK] El servicio de Ollama ya está activo y respondiendo.")
            return True
    except Exception:
        pass

    log_tactical("[AVISO] El servicio de Ollama no responde. Intentando iniciar servicio de forma automática...")
    
    # Intentar levantar Ollama de forma invisible en segundo plano dependiendo de la plataforma
    if sys.platform == "darwin":
        # macOS: intentar ejecutar el binario CLI directamente en segundo plano para evitar abrir el icono del menú superior
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_tactical("[OK] Ejecutando 'ollama serve' en macOS en segundo plano...")
        except Exception:
            try:
                subprocess.Popen(["open", "-g", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log_tactical("[OK] Lanzando Ollama.app en macOS en segundo plano (fallback)...")
            except Exception:
                pass
    elif sys.platform.startswith("win"):
        # Windows: buscar en directorios comunes e iniciar como daemon ("serve") sin levantar icono en la barra de tareas
        rutas = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
            os.path.expandvars(r"%ProgramFiles%\Ollama\ollama.exe")
        ]
        iniciado = False
        for r in rutas:
            if os.path.exists(r):
                try:
                    subprocess.Popen([r, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    log_tactical(f"[OK] Lanzando daemon de Ollama desde {r} en segundo plano...")
                    iniciado = True
                    break
                except Exception:
                    pass
        if not iniciado:
            import shutil
            if shutil.which("ollama") is not None:
                try:
                    subprocess.Popen(["ollama", "serve"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    log_tactical("[OK] Ejecutando 'ollama serve' en Windows...")
                    iniciado = True
                except Exception:
                    pass
            else:
                if download_and_install_ollama_windows():
                    # Re-buscar en directorios comunes tras instalar y arrancar con "serve"
                    for r in rutas:
                        if os.path.exists(r):
                            try:
                                subprocess.Popen([r, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                log_tactical(f"[OK] Lanzando daemon de Ollama recién instalado desde {r}...")
                                iniciado = True
                                break
                            except Exception:
                                pass
    else:
        # Linux u otros
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_tactical("[OK] Ejecutando 'ollama serve' en Linux...")
        except Exception:
            pass

    # Esperar hasta 8 segundos en segundo plano a que responda el puerto
    for i in range(8):
        time.sleep(1.0)
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=1.0)
            if resp.status_code == 200:
                log_tactical("[OK] Servicio de Ollama iniciado exitosamente.")
                return True
        except Exception:
            pass
        log_tactical(f"Esperando respuesta de Ollama ({i+1}/8)...")
        
    log_tactical("[ADVERTENCIA] No se pudo comprobar que el servicio de Ollama esté respondiendo en localhost:11434.")
    return False

def verify_and_pull_ollama_model():
    """Verifica e inicia Ollama y baja el modelo en segundo plano de manera asíncrona."""
    try:
        # Asegurar primero que el servicio de Ollama esté iniciado
        start_ollama_service()
        
        log_tactical("Verificando si el modelo 'llama3' está instalado en Ollama...")
        import requests
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if any("llama3" in m for m in models):
                    log_tactical("[OK] El modelo 'llama3' está disponible localmente en el servidor.")
                    return
        except Exception:
            pass
            
        log_tactical("[AVISO] El modelo 'llama3' no está disponible. Iniciando descarga en segundo plano...")
        
        # Resolver ruta absoluta de Ollama en Windows si no está en PATH
        ollama_bin = "ollama"
        if sys.platform.startswith("win"):
            rutas_win = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                os.path.expandvars(r"%ProgramFiles%\Ollama\ollama.exe")
            ]
            for r in rutas_win:
                if os.path.exists(r):
                    ollama_bin = r
                    break
                    
        try:
            subprocess.run([ollama_bin, "pull", "llama3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            log_tactical("[OK] Modelo 'llama3' descargado correctamente en segundo plano.")
        except Exception as e:
            log_tactical(f"[ERROR] No se pudo descargar el modelo de forma automática. Detalle: {e}")
            log_tactical("Asegúrese de ejecutar manualmente: 'ollama pull llama3' si desea usar la IA.")
    except Exception as e:
        log_tactical(f"[AVISO] La inicialización asíncrona de Ollama reportó incidencias: {e}")

def launch_app():
    log_tactical("Iniciando servidor Streamlit de FODA S5...")
    try:
        if hasattr(sys, "_MEIPASS"):
            # Modo empaquetado (PyInstaller)
            import streamlit.web.bootstrap
            main_script = os.path.join(getattr(sys, "_MEIPASS"), "main.py")
            streamlit.web.bootstrap.run(main_script, False, [], {})
        else:
            # Modo desarrollo
            subprocess.run([sys.executable, "-m", "streamlit", "run", "main.py"])
    except KeyboardInterrupt:
        log_tactical("Servidor FODA S5 finalizado por el operador.")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    print("=====================================================================")
    print("                 FODA S5 - INICIALIZADOR DE SISTEMA                  ")
    print("=====================================================================")
    # 1. Comprobar dependencias primero (rápidamente sin consultar PyPI si ya existen)
    check_and_install_requirements()
    
    # 2. Configurar acceso directo en el Escritorio en Windows
    create_windows_shortcut()
    
    # 3. Levantar el servicio de Ollama y verificar modelos de forma Asíncrona (en background)
    # Esto evita congelar el arranque por latencias de red o esperas de puertos
    threading.Thread(target=verify_and_pull_ollama_model, daemon=True).start()
    
    # 4. Lanzar Streamlit al instante
    print("=====================================================================")
    launch_app()
