import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

RAIZ = Path(__file__).resolve().parent

VERDE = "#0b6b4d"
VERDE_OSCURO = "#085a40"
VERDE_CLARO = "#bff0d8"
FONDO = "#eef6f2"
GRIS = "#6b7280"
TEXTO = "#111827"

def carpeta_salida_para(ruta_video):
    if ruta_video.parent.name.lower() == "video":
        return ruta_video.parent.parent
    return ruta_video.parent / "resultados"

def etiqueta(padre, texto, tamano=10, negrita=False, color=TEXTO):
    estilo = "bold" if negrita else "normal"
    return tk.Label(
        padre, text=texto, bg="white", fg=color,
        font=("Segoe UI", tamano, estilo), anchor="w", justify="left",
    )

def boton(padre, texto, comando, principal=True):
    if principal:
        return tk.Button(
            padre, text=texto, command=comando, bg=VERDE, fg="white",
            activebackground=VERDE_OSCURO, activeforeground="white",
            relief="flat", font=("Segoe UI", 10, "bold"), padx=16, pady=8, cursor="hand2",
        )
    return tk.Button(
        padre, text=texto, command=comando, bg="white", fg=TEXTO,
        relief="solid", borderwidth=1, font=("Segoe UI", 10), padx=14, pady=6, cursor="hand2",
    )

class TarjetaProcesamiento:
    def __init__(self, ventana):
        self.ventana = ventana
        self.cola = queue.Queue()
        self.proceso = None
        self.ruta_video = None
        self.carpeta_salida = None
        self.finalizo = False
        self.construir_ventana()
        self.revisar_cola()
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

    def construir_ventana(self):
        self.ventana.title("AgroScan - Procesamiento (prototipo)")
        self.ventana.geometry("820x560")
        self.ventana.configure(bg=FONDO)
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Verde.Horizontal.TProgressbar",
            troughcolor="#e5e7eb", background=VERDE, bordercolor="#e5e7eb",
            lightcolor=VERDE, darkcolor=VERDE,
        )

        tk.Label(
            self.ventana, text="Procesamiento", bg=FONDO, fg=TEXTO,
            font=("Segoe UI", 16, "bold"), anchor="w",
        ).pack(fill="x", padx=24, pady=(18, 8))

        tarjeta = tk.Frame(
            self.ventana, bg="white", highlightbackground="#d1d5db", highlightthickness=1
        )
        tarjeta.pack(fill="x", padx=24, pady=8)
        interior = tk.Frame(tarjeta, bg="white")
        interior.pack(fill="x", padx=22, pady=18)
        etiqueta(interior, "Preprocesamiento de imágenes", tamano=12, negrita=True).pack(fill="x")
        descripcion = etiqueta(
            interior,
            "Extrae del video los frames necesarios para el mosaico, analiza su calidad, "
            "corrige solo lo necesario y guarda las imágenes con sus metadatos dentro.",
            color=GRIS,
        )
        descripcion.config(wraplength=730)
        descripcion.pack(fill="x", pady=(2, 12))

        fila_video = tk.Frame(interior, bg="white")
        fila_video.pack(fill="x", pady=4)
        etiqueta(fila_video, "Video:", negrita=True).pack(side="left")
        self.texto_video = etiqueta(fila_video, "Ninguno seleccionado", color=GRIS)
        self.texto_video.pack(side="left", padx=8)
        boton(fila_video, "Elegir video...", self.elegir_video, principal=False).pack(side="right")

        fila_salida = tk.Frame(interior, bg="white")
        fila_salida.pack(fill="x", pady=4)
        etiqueta(fila_salida, "Resultados en:", negrita=True).pack(side="left")
        self.texto_salida = etiqueta(fila_salida, "-", color=GRIS)
        self.texto_salida.pack(side="left", padx=8)

        self.boton_iniciar = boton(interior, "Iniciar preprocesamiento", self.iniciar)
        self.boton_iniciar.pack(anchor="w", pady=(14, 8))
        self.boton_iniciar.config(state="disabled")

        self.texto_etapa = etiqueta(interior, "Listo para iniciar", negrita=True)
        self.texto_etapa.pack(fill="x", pady=(8, 4))
        self.barra = ttk.Progressbar(
            interior, style="Verde.Horizontal.TProgressbar",
            mode="determinate", maximum=100, length=700,
        )
        self.barra.pack(fill="x")
        self.texto_porcentaje = etiqueta(interior, "0 %", color=GRIS)
        self.texto_porcentaje.pack(anchor="e", pady=(2, 0))

        self.marco_resultado = tk.Frame(interior, bg="white")
        self.marco_resultado.pack(fill="x", pady=(10, 0))
        self.boton_abrir = boton(
            interior, "Abrir carpeta de resultados", self.abrir_carpeta, principal=False
        )

        self.texto_error = etiqueta(interior, "", color="#b91c1c")
        self.texto_error.config(wraplength=730)
        self.texto_error.pack(fill="x", pady=(8, 0))

    def elegir_video(self):
        ruta = filedialog.askopenfilename(
            title="Elegir video", filetypes=[("Videos MP4", "*.mp4 *.MP4")]
        )
        if not ruta:
            return
        self.ruta_video = Path(ruta)
        self.carpeta_salida = carpeta_salida_para(self.ruta_video)
        self.texto_video.config(text=self.ruta_video.name, fg=TEXTO)
        self.texto_salida.config(text=str(self.carpeta_salida))
        self.boton_iniciar.config(state="normal")

    def iniciar(self):
        self.finalizo = False
        self.boton_iniciar.config(state="disabled")
        self.texto_error.config(text="")
        self.boton_abrir.pack_forget()
        for elemento in self.marco_resultado.winfo_children():
            elemento.destroy()
        self.mostrar_progreso(0, "Preparando video")
        hilo = threading.Thread(target=self.ejecutar, daemon=True)
        hilo.start()

    def abrir_carpeta(self):
        os.startfile(str(self.carpeta_salida))

    def cerrar(self):
        if self.proceso is not None and self.proceso.poll() is None:
            self.proceso.terminate()
        self.ventana.destroy()

    def ejecutar(self):
        comando = [
            sys.executable, str(RAIZ / "main.py"),
            "--video", str(self.ruta_video),
            "--salida", str(self.carpeta_salida),
            "--json",
        ]
        try:
            self.proceso = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,   # el log detallado se descarta aquí
                text=True,
                encoding="utf-8",
                cwd=str(RAIZ),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for linea in self.proceso.stdout:
                try:
                    self.cola.put(json.loads(linea))
                except ValueError:
                    pass    # una línea que no es JSON se ignora
            self.proceso.wait()
            self.cola.put({"tipo": "termino", "codigo": self.proceso.returncode})
        except Exception as error:
            self.cola.put({"tipo": "error", "mensaje": str(error)})

    def revisar_cola(self):
        while True:
            try:
                evento = self.cola.get_nowait()
            except queue.Empty:
                break
            self.procesar_evento(evento)
        self.ventana.after(100, self.revisar_cola)

    def procesar_evento(self, evento):
        tipo = evento.get("tipo")
        if tipo == "progreso":
            self.mostrar_progreso(evento["porcentaje"], evento["etapa"])

        elif tipo == "fin":
            self.finalizo = True
            self.mostrar_progreso(100, "Preprocesamiento completado")
            self.mostrar_resultado(evento["resumen"])
            self.boton_iniciar.config(state="normal")

        elif tipo == "error":
            self.finalizo = True
            self.texto_error.config(text=f"Error: {evento['mensaje']}")
            self.boton_iniciar.config(state="normal")

        elif tipo == "termino" and not self.finalizo:
            self.texto_error.config(
                text=f"El proceso terminó de forma inesperada (código {evento['codigo']})"
            )
            self.boton_iniciar.config(state="normal")

    def mostrar_progreso(self, porcentaje, etapa):
        self.barra["value"] = porcentaje
        self.texto_etapa.config(text=etapa)
        self.texto_porcentaje.config(text=f"{porcentaje} %")

    def mostrar_resultado(self, resumen):
        textos = [
            f"{resumen['imagenes_finales']} imágenes",
            f"{resumen['modificadas']} modificadas",
            f"{resumen['con_advertencias']} con advertencias",
        ]
        if resumen["con_pendientes"] > 0:
            textos.append(f"{resumen['con_pendientes']} con problemas pendientes")
        if resumen["plan_b"]:
            textos.append("Plan B: sin imágenes finales")
        for texto in textos:
            tk.Label(
                self.marco_resultado, text=texto, bg=VERDE_CLARO, fg=VERDE,
                font=("Segoe UI", 9, "bold"), padx=12, pady=4,
            ).pack(side="left", padx=(0, 8))
        self.boton_abrir.pack(anchor="w", pady=(12, 0))

def main():
    ventana = tk.Tk()
    TarjetaProcesamiento(ventana)
    ventana.mainloop()

if __name__ == "__main__":
    main()