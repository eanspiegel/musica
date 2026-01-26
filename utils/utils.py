import os

class Utils:
    """Funciones de utilidad estáticas."""
    
    @staticmethod
    def formatear_tamano(bytes_val: float) -> str:
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unidad}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} TB"

    @staticmethod
    def verificar_ffmpeg() -> bool:
        try:
            import subprocess
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            resultado = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True,
                startupinfo=startupinfo,
                timeout=3
            )
            return resultado.returncode == 0
        except:
            return False
