# main.py
# Punto de entrada del módulo de preprocesamiento. Dos formas de usarlo:
#
#   python main.py
#       Prueba: procesa el primer video de data/videos y muestra texto legible.
#
#   python main.py --video RUTA_VIDEO --salida CARPETA_SALIDA --json
#       Uso desde otra aplicación: escribe una línea JSON por evento.

import argparse
import json
import sys
from pathlib import Path

from src import config
from src import gestor_carpetas
from src import proceso
from src import video


def leer_argumentos():
    """Lee los argumentos con los que se ejecutó el programa."""
    parser = argparse.ArgumentParser(
        description="Preprocesamiento de imágenes aéreas de AgroScan"
    )
    parser.add_argument("--video", help="Ruta del video MP4 a procesar")
    parser.add_argument("--salida", help="Carpeta donde se guardarán los resultados")
    parser.add_argument(
        "--json", action="store_true",
        help="Escribir el avance como líneas JSON (para otra aplicación)",
    )
    return parser.parse_args()


def avance_texto(porcentaje, mensaje):
    """Muestra el avance en texto legible."""
    if porcentaje % 5 == 0:
        print(f"[{porcentaje:3d}%] {mensaje}", flush=True)


def avance_json(porcentaje, mensaje):
    """Escribe el avance como una línea JSON."""
    evento = {"tipo": "progreso", "porcentaje": porcentaje, "etapa": mensaje}
    print(json.dumps(evento), flush=True)


def mostrar_error(mensaje, formato_json):
    """Informa un error, en texto o en JSON."""
    if formato_json:
        print(json.dumps({"tipo": "error", "mensaje": mensaje}), flush=True)
    else:
        print(f"ERROR: {mensaje}", flush=True)


def mostrar_fin(resumen, formato_json):
    """Informa que el proceso terminó, con el resumen."""
    if formato_json:
        evento = {"tipo": "fin", "porcentaje": 100, "resumen": resumen}
        print(json.dumps(evento), flush=True)
    else:
        print("\nResumen:")
        for nombre, valor in resumen.items():
            print(f"  {nombre}: {valor}")


def main():
    args = leer_argumentos()
    gestor_carpetas.crear_carpetas_de_trabajo()

    # Elegir el video
    if args.video is None:
        videos = video.buscar_videos()
        if len(videos) == 0:
            mostrar_error("No hay videos MP4 en la carpeta data/videos", args.json)
            sys.exit(1)
        ruta_video = videos[0]
    else:
        ruta_video = Path(args.video)

    # Elegir la carpeta de salida
    if args.salida is None:
        carpeta_salida = config.CARPETA_DATOS / "salidas" / ruta_video.stem
    else:
        carpeta_salida = Path(args.salida)

    al_avanzar = avance_json if args.json else avance_texto

    try:
        resumen = proceso.procesar_video(ruta_video, carpeta_salida, al_avanzar)
    except Exception as error:
        mostrar_error(str(error), args.json)
        sys.exit(1)

    mostrar_fin(resumen, args.json)


if __name__ == "__main__":
    main()