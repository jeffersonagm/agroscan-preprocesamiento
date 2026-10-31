from src import config

def crear_carpetas_de_trabajo():
    for carpeta in config.CARPETAS_DE_TRABAJO:
        if carpeta.exists():
            print(f"Ya existe: {carpeta}")
        else:
            carpeta.mkdir(parents=True)
            print(f"Creada: {carpeta}")

def crear_carpeta_de_mision(carpeta_base, ruta_video):
    carpeta = carpeta_base / ruta_video.stem
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta