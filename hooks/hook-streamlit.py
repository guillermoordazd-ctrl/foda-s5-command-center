# type: ignore
from PyInstaller.utils.hooks import copy_metadata, collect_submodules, collect_data_files

# Copiar metadatos para evitar el error PackageNotFoundError en Streamlit
datas = copy_metadata('streamlit') + collect_data_files('streamlit')

# Recopilar todos los submódulos de streamlit de forma estática
hiddenimports = collect_submodules('streamlit')
