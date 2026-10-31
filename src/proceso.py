from pathlib import Path
from src import calidad
from src import config
from src import finales
from src import gestor_carpetas
from src import metadatos
from src import recorrido
from src import seleccion
from src import video
from src.logger import configurar_logger

def _avisar(al_avanzar, porcentaje, mensaje):
    """Informa el avance, si alguien está escuchando."""
    if al_avanzar is not None:
        al_avanzar(porcentaje, mensaje)

def procesar_video(ruta_video, carpeta_salida, al_avanzar=None):
    ruta_video = Path(ruta_video)
    carpeta_salida = Path(carpeta_salida)
    gestor_carpetas.crear_carpetas_de_trabajo()
    log = configurar_logger()
    _avisar(al_avanzar, 0, "Preparando video")
    if not ruta_video.exists():
        raise FileNotFoundError(f"No existe el video: {ruta_video}")
    carpeta_frames = carpeta_salida / config.SUBCARPETA_FRAMES
    carpeta_finales = carpeta_salida / config.SUBCARPETA_FINALES
    carpeta_frames.mkdir(parents=True, exist_ok=True)
    carpeta_finales.mkdir(parents=True, exist_ok=True)
    log.info(f"Video: {ruta_video}")
    log.info(f"Carpeta de salida: {carpeta_salida}")
    info = video.obtener_info_video(ruta_video)
    log.info(f"FPS: {info['fps']:.2f} | Resolución: {info['ancho']}x{info['alto']}")
    log.info(f"Duración: {info['duracion_segundos']:.1f} s | Frames totales: {info['total_frames']}")

    _avisar(al_avanzar, config.PROGRESO_FIN_PREPARAR, "Analizando video")
    log.info("Midiendo el movimiento del recorrido (puede tardar unos minutos)...")
    pasos = recorrido.medir_recorrido(ruta_video, config.PASO_MEDICION_FRAMES)

    no_confiables = 0
    for paso in pasos:
        if not paso["confiable"]:
            no_confiables += 1
    log.info(f"Pasos medidos: {len(pasos)} | no confiables: {no_confiables}")
    giro_maximo = 0.0
    for paso in pasos:
        if paso["confiable"] and abs(paso["angulo"]) > giro_maximo:
            giro_maximo = abs(paso["angulo"])
    log.info(f"Giro máximo entre mediciones: {giro_maximo:.2f}°")
    if giro_maximo > config.GIRO_MAXIMO_ESPERADO:
        log.warning("Giro grande detectado: revisar la orientación de las imágenes")
    elegidos = seleccion.seleccionar_frames(pasos)
    log.info(f"Frames seleccionados: {len(elegidos)}")
    resumen = {
        "video": ruta_video.name,
        "imagenes_originales": 0,
        "imagenes_finales": 0,
        "modificadas": 0,
        "con_pendientes": 0,
        "con_advertencias": 0,
        "carpeta_frames": str(carpeta_frames),
        "carpeta_finales": str(carpeta_finales),
        "plan_b": False,
    }

    _avisar(al_avanzar, config.PROGRESO_FIN_MEDIR, "Extrayendo imágenes")
    log.info("Guardando frames...")

    if len(elegidos) == 0:
        log.warning("No se detectó movimiento; se usa el intervalo fijo de respaldo")
        resumen["plan_b"] = True
        total = video.extraer_frames(
            ruta_video, carpeta_frames, config.INTERVALO_EXTRACCION_SEGUNDOS
        )
    else:
        metadatos.agregar_posicion_en_pasada(elegidos)
        fecha_inicio = metadatos.calcular_fecha_inicio(ruta_video, info["duracion_segundos"])
        imagenes = {}
        textos_por_frame = {}
        for dato in elegidos:
            textos = metadatos.crear_textos(dato, ruta_video.name, fecha_inicio, info["fps"])
            textos_por_frame[dato["frame"]] = textos
            imagenes[dato["frame"]] = {
                "nombre": metadatos.crear_nombre_archivo(dato, ruta_video.stem),
                "exif": metadatos.crear_exif(textos),
            }
        total = video.extraer_frames_elegidos(ruta_video, carpeta_frames, imagenes)
    resumen["imagenes_originales"] = total
    log.info(f"Frames guardados: {total} en {carpeta_frames}")

    _avisar(al_avanzar, config.PROGRESO_FIN_GUARDAR, "Analizando calidad de las imágenes")
    log.info("Analizando la calidad de las imágenes...")
    rutas_imagenes = sorted(carpeta_frames.glob("*.jpg"))
    resultados, referencia = calidad.analizar_imagenes(rutas_imagenes)
    sin_ajustes = 0
    con_advertencias = 0
    for nombre, resultado in resultados.items():
        diagnostico = resultado["diagnostico"]
        if len(diagnostico["ajustes"]) == 0:
            sin_ajustes += 1
        else:
            log.info(f"{nombre}: necesita ajustes {diagnostico['ajustes']}")

        if len(diagnostico["advertencias"]) > 0:
            con_advertencias += 1
            log.info(f"{nombre}: advertencias {diagnostico['advertencias']}")
    resumen["con_advertencias"] = con_advertencias
    log.info(
        f"Calidad: {sin_ajustes} de {len(resultados)} imágenes sin ajustes | "
        f"{con_advertencias} con advertencias"
    )

    if len(elegidos) == 0:
        log.warning("Sin datos del recorrido (plan B): no se generan las imágenes finales")
    else:
        _avisar(al_avanzar, config.PROGRESO_FIN_CALIDAD, "Ajustando detalles visuales")
        log.info("Generando las imágenes finales...")
        trabajos = {}
        for dato in elegidos:
            frame = dato["frame"]
            nombre = imagenes[frame]["nombre"]
            trabajos[frame] = {
                "nombre": nombre,
                "textos": textos_por_frame[frame],
                "diagnostico": resultados[nombre]["diagnostico"],
            }
        lista_resumen = finales.generar_imagenes_finales(
            ruta_video, carpeta_finales, trabajos, referencia
        )
        modificadas = 0
        con_pendientes = 0
        for item in lista_resumen:
            if len(item["aplicados"]) > 0:
                modificadas += 1
                log.info(f"{item['nombre']}: se aplicó {item['aplicados']}")
            if len(item["pendientes"]) > 0:
                con_pendientes += 1
                log.warning(f"{item['nombre']}: queda pendiente {item['pendientes']}")
        resumen["imagenes_finales"] = len(lista_resumen)
        resumen["modificadas"] = modificadas
        resumen["con_pendientes"] = con_pendientes
        log.info(f"Imágenes finales guardadas: {len(lista_resumen)} en {carpeta_finales}")
        log.info(f"Modificadas: {modificadas} | con problemas pendientes: {con_pendientes}")

    _avisar(al_avanzar, 100, "Preprocesamiento completado")
    log.info("Preprocesamiento completado.")
    return resumen