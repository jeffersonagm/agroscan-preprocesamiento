# AgroScan - Módulo de preprocesamiento de imágenes aéreas

Toma un video MP4 grabado por un dron (DJI Mini 3), extrae los frames necesarios para
generar un ortomosaico, analiza la calidad de cada imagen, corrige únicamente lo que
haga falta y guarda las imágenes finales con su información dentro (metadatos EXIF).
Opcionalmente las envía a un servidor mediante una API REST. El procesamiento local no
depende de Internet.

## Cómo funciona

```
Video MP4
  -> medir el movimiento a lo largo del recorrido (avance, retroceso, lateral)
  -> seleccionar frames con un solape frontal mínimo del 75 %
  -> guardar los frames originales (con sus metadatos)
  -> diagnosticar la calidad de cada imagen
  -> corregir solo lo necesario (brillo, contraste, nitidez)
  -> guardar las imágenes finales (con calidad y ajustes en sus metadatos)
  -> sincronizar con el servidor (opcional)
```

## Requisitos e instalación

Desarrollado y probado con Python 3.15.1, opencv-python 5.0.0.93, numpy 2.5.4 y
pillow 13.0.0 (ver `requirements.txt`).

    python -m venv venv
    venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Uso

**Modo prueba:** procesa el primer video de `data/videos/`.

    python main.py

**Modo aplicación:**

    python main.py --video "RUTA\video.mp4" --salida "RUTA\carpeta_salida" --json
    python main.py --video ... --salida ... --servidor http://HOST:PUERTO --json
    python main.py --salida ... --servidor ... --solo-sincronizar --json

| Argumento | Descripción |
|---|---|
| `--video` | Ruta del video MP4 a procesar |
| `--salida` | Carpeta donde se guardan los resultados |
| `--servidor` | Dirección del servidor al que enviar las imágenes (opcional) |
| `--mision` | Identificador de la misión en el servidor (opcional; por defecto se deduce de la carpeta) |
| `--solo-sincronizar` | No procesa: solo envía lo que falte de una salida ya procesada |
| `--json` | Escribe el avance como líneas JSON |

### Comunicación con otra aplicación

Con `--json`, el programa escribe en la salida estándar **una línea JSON por evento**:

    {"tipo": "progreso", "porcentaje": 35, "etapa": "Extrayendo imágenes"}
    {"tipo": "error", "mensaje": "No existe el video: ..."}
    {"tipo": "fin", "porcentaje": 100, "resumen": {"imagenes_finales": 85, ...}}

- El registro detallado sale por la salida de errores (stderr) y se guarda en `data/logs/`.
  La aplicación debe leer o descartar stderr; si no, el proceso podría bloquearse.
- Código de salida: 0 si terminó bien, 1 si hubo un error.
- Etapas: Preparando video, Analizando video, Extrayendo imágenes, Analizando calidad de
  las imágenes, Ajustando detalles visuales, Sincronizando archivos.
- `interfaz_prueba.py` es un cliente de ejemplo que cumple este contrato.

## Resultados

Dentro de la carpeta de salida:

    frames_originales/     frames tal como salen del video (con metadatos)
    imagenes_procesadas/   imágenes finales, las que debe usar el módulo de análisis
    estado_sincronizacion.json   estado de envío de cada imagen (si se usa --servidor)

Nombre de cada imagen: `<video>_P<pasada>_I<número en la pasada>_F<frame>.jpg`. El orden
alfabético coincide con el orden del recorrido.

### Información dentro de cada imagen (Propiedades > Detalles)

| Campo | Contenido |
|---|---|
| Título | Pasada e imagen dentro de la pasada |
| Fecha de toma | Estimada: fecha del archivo de video más el segundo del frame |
| Programa | Nombre del módulo |
| Asunto | Descripción de la imagen |
| Comentarios | Video, frame, segundo, pasada y sentido, solape con la imagen anterior, ajustes aplicados, problemas pendientes y advertencias |

No se incluyen coordenadas geográficas.

## Criterios de calidad

El diagnóstico distingue **ajustes** (se corrigen) de **advertencias** (solo se informan).

| Parámetro | Valor |
|---|---|
| Brillo | ±25 % de la mediana de la misión; absoluto 60 a 200 |
| Contraste | -25 % de la mediana; mínimo absoluto 25 |
| Nitidez | 35 % de la mediana (nitidez normalizada por el contraste) |
| Píxeles quemados u oscuros | Advertencia si superan el 5 % |
| Iluminación desigual | Advertencia si supera el 25 % |
| Esquinas respecto al centro | Advertencia si bajan del 70 % |

Las sombras se informan pero **no se corrigen**: son parte real de la escena. Todos los
valores están en `src/config.py` y son provisionales (calibrados con dos vuelos).

## Pruebas

    python -m unittest discover -s pruebas -t . -v

Pruebas manuales (con videos reales): `python -m pruebas.manuales.<nombre>`.
Para probar el envío sin servidor real: `python servidor_prueba.py` (requiere Flask,
ver `requirements-dev.txt`).

## Estructura del proyecto

    main.py               punto de entrada (línea de comandos)
    src/proceso.py        flujo completo (procesar_video, sincronizar_salida)
    src/video.py          lectura del video y guardado de frames
    src/movimiento.py     movimiento entre dos imágenes
    src/recorrido.py      medición y clasificación del recorrido
    src/seleccion.py      selección de frames
    src/metadatos.py      nombres y metadatos EXIF
    src/calidad.py        medidas y diagnóstico de calidad
    src/mejora.py         correcciones de brillo, contraste y nitidez
    src/finales.py        generación de las imágenes finales
    src/sincronizacion.py envío al servidor con reintentos y estado
    src/config.py         parámetros
    interfaz_prueba.py    prototipo de interfaz (Tkinter)
    servidor_prueba.py    servidor de mentira para pruebas

## Limitaciones conocidas

- Calibrado con dos vuelos; los umbrales deben revisarse con otros cultivos, alturas y horas.
- No hay ejemplos de desenfoque real: el umbral de nitidez se calibró con desenfoques artificiales.
- Las correcciones se validaron con degradaciones artificiales (en los vuelos reales ninguna imagen las necesitó).
- Se asume que el dron avanza en el sentido vertical de la imagen; si no, se usa el plan B (intervalo fijo).
- La fecha de cada imagen es una estimación.
- Con la combinación de versiones usada se observó, una vez, un error interno de OpenCV
  al convertir frames en la etapa final; por eso esa etapa usa la lectura estándar.

## Por confirmar con el equipo

- Cómo ejecuta la aplicación el módulo (Python instalado o empaquetado) y desde qué carpeta.
- Dónde guarda y lee los resultados cada salida.
- Origen de la fecha de cada imagen (fecha del video o dato del registro).
- API real del servidor (dirección, autenticación y nombres de los campos).