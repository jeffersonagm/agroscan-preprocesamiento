# AgroScan - Módulo de preprocesamiento de imágenes aéreas

Toma un video MP4 de un dron, extrae los frames necesarios para un ortomosaico,
analiza su calidad, corrige solo lo necesario y guarda las imágenes finales con
sus metadatos dentro (EXIF).

## Instalación

    python -m venv venv
    venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Uso

Copiar un video MP4 en `data/videos/` y ejecutar:

    python main.py

## Estructura

- `main.py`: punto de entrada.
- `src/`: módulos (video, recorrido, selección de frames, metadatos, calidad, mejora).
- `data/`: videos y resultados (no se sube a Git).

## Estado

Sprints 1 a 6 completados. En desarrollo: interfaz y envío por API REST.