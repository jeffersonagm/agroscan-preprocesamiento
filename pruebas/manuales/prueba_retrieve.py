import io
import re
import sys
import time
from pathlib import Path

import cv2
from PIL import Image

ruta_video = sys.argv[1]
carpeta = Path(sys.argv[2])

# Los números de frame están en el nombre de cada imagen (..._F001248.jpg)
frames = set()
for ruta in carpeta.glob("*.jpg"):
    coincidencia = re.search(r"_F(\d{6})\.jpg$", ruta.name)
    if coincidencia:
        frames.add(int(coincidencia.group(1)))

ultimo = max(frames)
print(f"{len(frames)} frames a leer, hasta el {ultimo}")

for vuelta in (1, 2, 3):
    captura = cv2.VideoCapture(str(ruta_video))
    indice = 0
    leidos = 0
    inicio = time.perf_counter()
    try:
        while indice <= ultimo:
            if not captura.grab():
                break
            if indice in frames:
                hay_imagen, frame = captura.retrieve()
                if not hay_imagen:
                    raise RuntimeError("retrieve devolvió falso")
                imagen = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imagen.save(io.BytesIO(), format="JPEG", quality=95)   # codifica sin escribir a disco
                leidos += 1
            indice += 1
    except Exception as error:
        print(f"Vuelta {vuelta}: ERROR en el frame {indice} ({leidos} leídos): "
              f"{type(error).__name__}: {error}")
    else:
        print(f"Vuelta {vuelta}: OK, {leidos} frames en {time.perf_counter() - inicio:.1f} s")
    captura.release()