import os
import sys
import json
from typing import Optional

class ConfigManager:
    """Gestiona la configuración de la aplicación y persistencia de datos."""
    
    def __init__(self):
        self.config_file = 'config.json'
        self.base_path = self._obtener_ruta_base()
        self.config_path = os.path.join(self.base_path, self.config_file)

    def _obtener_ruta_base(self) -> str:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def cargar_configuracion(self) -> Optional[str]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return data.get('ruta_descarga')
            except Exception as e:
                print(f"Error al leer configuración: {e}")
                return None
        return None

    def guardar_configuracion(self, ruta: str) -> None:
        try:
            with open(self.config_path, 'w') as f:
                json.dump({'ruta_descarga': ruta}, f)
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
