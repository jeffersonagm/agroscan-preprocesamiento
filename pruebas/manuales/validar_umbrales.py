import re
from PIL import Image
from src import calidad, config

SALIDAS = config.CARPETA_DATOS / "salidas"
MISIONES = {
    "Vuelo 1 (video de prueba)": SALIDAS / "AgroScan-mision-2026-10-26",
    "Vuelo 2 (DJI_0104)": SALIDAS / "DJI_real",
}

def leer_solape_minimo(carpeta_finales):
    solapes = []
    for ruta in sorted(carpeta_finales.glob("*.jpg")):
        valor = Image.open(ruta).getexif().get(0x9C9C)
        if isinstance(valor, tuple):
            valor = bytes(valor)
        if isinstance(valor, bytes):
            texto = valor.decode("utf-16-le")
            coincidencia = re.search(r"Solape con la imagen anterior: ([0-9.]+) %", texto)
            if coincidencia:
                solapes.append(float(coincidencia.group(1)))
    if len(solapes) == 0:
        return None
    return min(solapes)

for nombre, carpeta in MISIONES.items():
    rutas = sorted((carpeta / config.SUBCARPETA_FRAMES).glob("*.jpg"))
    if len(rutas) == 0:
        print(f"\n=== {nombre}: no se encontraron imágenes en {carpeta} ===")
        continue
    print(f"\n=== {nombre} ({len(rutas)} imágenes) ===")
    resultados, referencia = calidad.analizar_imagenes(rutas)
    medidas = [resultado["medidas"] for resultado in resultados.values()]
    brillos = [m["brillo"] for m in medidas]
    desviacion = [b / referencia["brillo"] - 1 for b in brillos]
    print(
        f"Brillo: mediana {referencia['brillo']:.1f} | rango {min(brillos):.1f} a {max(brillos):.1f} | "
        f"desviación {min(desviacion) * 100:+.1f} % a {max(desviacion) * 100:+.1f} % "
        f"(tolerancia ±{config.TOLERANCIA_BRILLO * 100:.0f} %; límites absolutos "
        f"{config.BRILLO_MINIMO} a {config.BRILLO_MAXIMO})"
    )

    contrastes = [m["contraste"] for m in medidas]
    desviacion = [c / referencia["contraste"] - 1 for c in contrastes]
    print(
        f"Contraste: mediana {referencia['contraste']:.1f} | mínimo {min(contrastes):.1f} | "
        f"desviación mínima {min(desviacion) * 100:+.1f} % "
        f"(tolerancia -{config.TOLERANCIA_CONTRASTE * 100:.0f} %; mínimo absoluto {config.CONTRASTE_MINIMO})"
    )

    nitidez = [m["nitidez_norm"] / referencia["nitidez_norm"] for m in medidas]
    print(
        f"Nitidez: la más baja está al {min(nitidez) * 100:.1f} % de la mediana "
        f"(umbral {config.NITIDEZ_MINIMA_RELATIVA * 100:.0f} %)"
    )

    quemado = max(m["pct_quemado"] for m in medidas)
    oscuro = max(m["pct_oscuro"] for m in medidas)
    print(
        f"Exposición: píxeles quemados, máximo {quemado:.2f} % | píxeles oscuros, máximo {oscuro:.2f} % "
        f"(límite {config.PCT_EXTREMOS_MAXIMO} %)"
    )

    desigualdad = max(m["desigualdad"] for m in medidas)
    sobre_desigualdad = sum(1 for m in medidas if m["desigualdad"] > config.DESIGUALDAD_MAXIMA)
    esquinas = min(m["esquinas_vs_centro"] for m in medidas)
    bajo_esquinas = sum(1 for m in medidas if m["esquinas_vs_centro"] < config.ESQUINAS_MINIMO)
    print(
        f"Iluminación desigual: máximo {desigualdad:.1f} % (límite {config.DESIGUALDAD_MAXIMA:.0f} %): "
        f"{sobre_desigualdad} imágenes por encima"
    )
    print(
        f"Esquinas respecto al centro: mínimo {esquinas:.1f} % (límite {config.ESQUINAS_MINIMO:.0f} %): "
        f"{bajo_esquinas} imágenes por debajo"
    )

    con_ajustes = sum(1 for r in resultados.values() if len(r["diagnostico"]["ajustes"]) > 0)
    print(f"Imágenes que necesitarían ajustes: {con_ajustes} de {len(rutas)}")
    solape = leer_solape_minimo(carpeta / config.SUBCARPETA_FINALES)
    if solape is None:
        print("Solape mínimo: no se pudo leer de los metadatos")
    else:
        print(
            f"Solape mínimo entre frames consecutivos (leído de los metadatos): {solape:.1f} % "
            f"(exigido: {config.SOLAPE_FRONTAL_MINIMO_PCT} %)"
        )