import unittest
from datetime import datetime
from src import metadatos

def dato(frame, pasada=1, sentido="avance", solape=77.2):
    return {"frame": frame, "pasada": pasada, "sentido": sentido, "solape": solape}

class PruebasMetadatos(unittest.TestCase):

    def test_nombre_de_archivo(self):
        d = {"frame": 64, "pasada": 1, "numero_en_pasada": 2}
        self.assertEqual(
            metadatos.crear_nombre_archivo(d, "DJI_0104"), "DJI_0104_P1_I002_F000064.jpg"
        )

    def test_posicion_dentro_de_cada_pasada(self):
        lista = [dato(0, 1), dato(64, 1), dato(128, 1), dato(200, 2), dato(264, 2)]
        metadatos.agregar_posicion_en_pasada(lista)
        self.assertEqual([d["numero_en_pasada"] for d in lista], [1, 2, 3, 1, 2])
        self.assertEqual([d["total_en_pasada"] for d in lista], [3, 3, 3, 2, 2])

    def test_textos_de_una_imagen(self):
        d = dato(90)
        d["numero_en_pasada"] = 2
        d["total_en_pasada"] = 3
        inicio = datetime(2026, 10, 28, 12, 0, 0)
        textos = metadatos.crear_textos(d, "video.mp4", inicio, 30.0)
        self.assertEqual(textos["titulo"], "Pasada 1 - Imagen 2 de 3")
        self.assertEqual(textos["fecha"], "2026:10:28 12:00:03")   # 90 frames a 30 FPS = 3 s
        self.assertIn("Solape con la imagen anterior: 77.2 %", textos["comentarios"])

    def test_primera_imagen_de_la_pasada_no_tiene_solape(self):
        d = dato(0, solape=None)
        d["numero_en_pasada"] = 1
        d["total_en_pasada"] = 3
        textos = metadatos.crear_textos(d, "video.mp4", datetime(2026, 10, 28), 30.0)
        self.assertIn("no aplica", textos["comentarios"])

    def test_plan_b_dice_que_no_se_midio_el_solape(self):
        d = dato(0, sentido="intervalo fijo", solape=None)
        d["numero_en_pasada"] = 1
        d["total_en_pasada"] = 72
        textos = metadatos.crear_textos(d, "video.mp4", datetime(2026, 10, 28), 30.0)
        self.assertIn("no medido", textos["comentarios"])

    def test_calidad_sin_cambios_dice_imagen_sin_modificar(self):
        textos = {"titulo": "t", "comentarios": "base", "fecha": "f"}
        nuevos = metadatos.agregar_calidad(textos, [], {"ajustes": [], "advertencias": []})
        self.assertIn("imagen sin modificar", nuevos["comentarios"])
        self.assertIn("Advertencias: ninguna", nuevos["comentarios"])
        self.assertEqual(textos["comentarios"], "base")   # el original no se altera

    def test_calidad_con_ajustes_y_advertencias(self):
        textos = {"titulo": "t", "comentarios": "base", "fecha": "f"}
        diagnostico = {"ajustes": ["poca_nitidez"], "advertencias": ["iluminacion_desigual"]}
        nuevos = metadatos.agregar_calidad(textos, ["nitidez (cantidad 0.8)"], diagnostico)
        self.assertIn("Ajustes aplicados: nitidez (cantidad 0.8)", nuevos["comentarios"])
        self.assertIn("Problemas pendientes: poca_nitidez", nuevos["comentarios"])
        self.assertIn("Advertencias: iluminacion_desigual", nuevos["comentarios"])

if __name__ == "__main__":
    unittest.main()