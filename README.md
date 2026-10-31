## Uso desde otra aplicación

    python main.py --video "RUTA\DJI_0104.MP4" --salida "RUTA\salida-1" --json

Escribe en la salida estándar una línea JSON por evento:

    {"tipo": "progreso", "porcentaje": 35, "etapa": "Extrayendo imágenes"}
    {"tipo": "error", "mensaje": "No existe el video: ..."}
    {"tipo": "fin", "porcentaje": 100, "resumen": {"imagenes_finales": 73, ...}}

- El log detallado sale por la salida de errores (stderr) y a `data/logs/`.
- Código de salida: 0 si terminó bien, 1 si hubo un error.
- Resultados: `<salida>/frames_originales/` e `<salida>/imagenes_procesadas/`.
  Las imágenes finales llevan sus metadatos dentro (EXIF); no hay archivos aparte.

  - La aplicación debe leer o descartar la salida de errores (stderr) del proceso:
  si no se consume, el proceso podría bloquearse cuando ese canal se llene.
- `interfaz_prueba.py` es un cliente de ejemplo que cumple este contrato (lanza
  main.py con --json y lee las líneas), además de mostrar el aspecto deseado.