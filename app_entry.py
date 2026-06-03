# app_entry.py
import os
import sys
import streamlit.web.bootstrap

if __name__ == "__main__":
    # Obtiene la ruta del archivo main.py dentro del paquete compilado
    base_path = os.path.dirname(__file__)
    main_script = os.path.join(base_path, "main.py")
    
    # Inicializa el servidor web de Streamlit apuntando a main.py
    sys.argv = ["streamlit", "run", main_script, "--global.developmentMode=false"]
    streamlit.web.bootstrap.run(main_script, False, [], flag_options={})