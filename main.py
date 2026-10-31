from src import calidad
from src import config
from src import finales
from src import gestor_carpetas
from src import metadatos
from src import recorrido
from src import seleccion
from src import video
from src.logger import configurar_logger

def main():
    gestor_carpetas.crear_carpetas_de_trabajo()
    log = configurar_logger()
    log.info("AgroScan El Carmen - Módulo de preprocesamiento de imágenes")
    videos = video.buscar_videos()
    if len(videos) == 0:
        log.error("No hay videos MP4 en la carpeta data/videos")
        return
    ruta_video = videos[0]
    log.info(f"Video seleccionado: {ruta_video.name}")

    try:
        info = video.obtener_info_video(ruta_video)
    except ValueError as error:
        log.error(error)
        return
    log.info(f"FPS: {info['fps']:.2f} | Resolución: {info['ancho']}x{info['alto']}")
    log.info(f"Duración: {info['duracion_segundos']:.1f} s | Frames totales: {info['total_frames']}")
    log.info("Midiendo el movimiento del recorrido (puede tardar unos minutos)...")
    pasos = recorrido.medir_recorrido(ruta_video, config.PASO_MEDICION_FRAMES)
    no_confiables = 0
    for paso in pasos:
        if not paso["confiable"]:
            no_confiables += 1
    log.info(f"Pasos medidos: {len(pasos)} | no confiables: {no_confiables}")
    archivo_pasos = config.CARPETA_METADATOS / f"{ruta_video.stem}_pasos.json"
    recorrido.guardar_pasos(pasos, archivo_pasos)

    giro_maximo = 0.0
    for paso in pasos:
        if paso["confiable"] and abs(paso["angulo"]) > giro_maximo:
            giro_maximo = abs(paso["angulo"])
    log.info(f"Giro máximo entre mediciones: {giro_maximo:.2f}°")
    if giro_maximo > config.GIRO_MAXIMO_ESPERADO:
        log.warning("Giro grande detectado: revisar la orientación de las imágenes")
    elegidos = seleccion.seleccionar_frames(pasos)
    log.info(f"Frames seleccionados: {len(elegidos)}")
    log.info("Guardando frames...")
    carpeta_frames = gestor_carpetas.crear_carpeta_de_mision(
        config.CARPETA_FRAMES_ORIGINALES, ruta_video
    )

    if len(elegidos) == 0:
        log.warning("No se detectó movimiento; se usa el intervalo fijo de respaldo")
        total = video.extraer_frames(
            ruta_video,
            carpeta_frames,
            config.INTERVALO_EXTRACCION_SEGUNDOS,
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
    log.info(f"Frames guardados: {total} en {carpeta_frames}")

    log.info("Analizando la calidad de las imágenes...")
    rutas_imagenes = sorted(carpeta_frames.glob("*.jpg"))
    resultados, referencia = calidad.analizar_imagenes(rutas_imagenes)
    log.info(
        f"Referencia de la misión: brillo {referencia['brillo']:.1f} | "
        f"contraste {referencia['contraste']:.1f}"
    )

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
    log.info(
        f"Calidad: {sin_ajustes} de {len(resultados)} imágenes sin ajustes | "
        f"{con_advertencias} con advertencias"
    )

    if len(elegidos) == 0:
        log.warning("Sin datos del recorrido (plan B): no se generan las imágenes finales")
    else:
        log.info("Generando las imágenes finales...")
        carpeta_finales = gestor_carpetas.crear_carpeta_de_mision(
            config.CARPETA_IMAGENES_PROCESADAS, ruta_video
        )
        trabajos = {}
        for dato in elegidos:
            frame = dato["frame"]
            nombre = imagenes[frame]["nombre"]
            trabajos[frame] = {
                "nombre": nombre,
                "textos": textos_por_frame[frame],
                "diagnostico": resultados[nombre]["diagnostico"],
            }
        resumen = finales.generar_imagenes_finales(
            ruta_video, carpeta_finales, trabajos, referencia
        )
        modificadas = 0
        con_pendientes = 0
        for item in resumen:
            if len(item["aplicados"]) > 0:
                modificadas += 1
                log.info(f"{item['nombre']}: se aplicó {item['aplicados']}")
            if len(item["pendientes"]) > 0:
                con_pendientes += 1
                log.warning(f"{item['nombre']}: queda pendiente {item['pendientes']}")
        log.info(f"Imágenes finales guardadas: {len(resumen)} en {carpeta_finales}")
        log.info(f"Modificadas: {modificadas} | con problemas pendientes: {con_pendientes}")
    log.info("Preprocesamiento completado.")

if __name__ == "__main__":
    main()