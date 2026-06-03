@echo off
title COMPILADOR DE CONTROL TACTICO FODA S5 A EXE
echo =====================================================================
echo           FODA S5 - GENERADOR DE BINARIO AUTOCONTENIDO (.EXE)        
echo =====================================================================
echo.

:: 1. Verificar si existe el entorno virtual de Python local
if exist .\stratcom_env\Scripts\activate.bat (
    echo [SYS] Activando entorno virtual local stratcom_env...
    call .\stratcom_env\Scripts\activate.bat
) else (
    echo [AVISO] No se detecto el entorno virtual local 'stratcom_env'.
    echo Se intentara compilar utilizando el interprete de Python global del sistema.
)
echo.

:: 2. Instalar requerimientos y PyInstaller
echo [SYS] Asegurando instalacion de dependencias y PyInstaller...
python -m pip install --upgrade pip
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller
echo.

:: 3. Ejecutar compilador PyInstaller
echo [SYS] Iniciando proceso de compilacion con PyInstaller...
echo [SYS] Empaquetando en modo Onefile (un solo ejecutable) y Windowed (sin consola)...
pyinstaller --clean --noconfirm --onedir --windowed --name="FODA_S5_Command_Center" --icon="my_foda_s5.ico" --exclude-module="tkinter" --exclude-module="unittest" --exclude-module="email" --exclude-module="http" --exclude-module="xml" --exclude-module="pydoc" --additional-hooks-dir="hooks" --add-data "main.py;." --add-data "pdf_utils.py;." --add-data "models.py;." --add-data "database.py;." --add-data "charts.py;." --add-data "nlp_mapper.py;." --add-data "styles.css;." --add-data ".streamlit;.streamlit" run_foda_s5.py

echo.
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ocurrio un fallo durante la compilacion del ejecutable.
    pause
    exit /b %ERRORLEVEL%
)

echo =====================================================================
echo       [OK] COMPILACION DE CONTROL TACTICO FODA S5 EXITOSA             
echo =====================================================================
echo.
echo El archivo ejecutable autocontenido se ha creado en la ruta:
echo --^> dist\FODA_S5_Command_Center.exe
echo.
echo Puede distribuir este archivo en cualquier maquina Windows sin Python.
echo.
pause
