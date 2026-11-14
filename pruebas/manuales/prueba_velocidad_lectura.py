import sys
import time
import cv2

TOTAL = 600
CADA = 16

def con_read(ruta):
    captura = cv2.VideoCapture(str(ruta))
    inicio = time.perf_counter()
    for indice in range(TOTAL):
        hay_frame, frame = captura.read()
        if not hay_frame:
            break
        if indice % CADA == 0:
            frame.mean()          # "usar" el frame
    captura.release()
    return time.perf_counter() - inicio


def con_grab(ruta):
    captura = cv2.VideoCapture(str(ruta))
    inicio = time.perf_counter()
    for indice in range(TOTAL):
        hay_frame = captura.grab()
        if not hay_frame:
            break
        if indice % CADA == 0:
            _, frame = captura.retrieve()
            frame.mean()
    captura.release()
    return time.perf_counter() - inicio


ruta = sys.argv[1]

# Se repite cada método dos veces: la primera lectura del archivo puede ser más lenta
for vuelta in (1, 2):
    tiempo_read = con_read(ruta)
    tiempo_grab = con_grab(ruta)
    print(
        f"Vuelta {vuelta}: read() {tiempo_read:.1f} s | grab()+retrieve() {tiempo_grab:.1f} s | "
        f"diferencia {100 * (1 - tiempo_grab / tiempo_read):+.0f} %"
    )