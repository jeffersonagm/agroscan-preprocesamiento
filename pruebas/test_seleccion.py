import unittest
from src import seleccion

def paso(frame, dx=0.0, dy=0.0):
    return {"frame": frame, "confiable": True, "dx": dx, "dy": dy,
            "angulo": 0.0, "puntos": 500}

class PruebasSeleccion(unittest.TestCase):

    def test_avance_constante_cumple_el_solape(self):
        pasos = [paso(16 * n, dy=6.0) for n in range(1, 21)]
        elegidos = seleccion.seleccionar_frames(pasos)
        self.assertEqual(elegidos[0]["frame"], 0)          # primer frame de la fase
        self.assertEqual(elegidos[-1]["frame"], 320)       # último frame de la fase
        self.assertIsNone(elegidos[0]["solape"])           # el primero no tiene anterior
        for dato in elegidos:
            self.assertEqual(dato["pasada"], 1)
            self.assertEqual(dato["sentido"], "avance")
        for dato in elegidos[1:]:
            self.assertGreaterEqual(dato["solape"], 75)    # solape mínimo garantizado

    def test_cambio_de_linea_no_genera_frames(self):
        pasos = [paso(16 * n, dy=6.0) for n in range(1, 11)]
        pasos += [paso(16 * n, dx=3.0, dy=0.5) for n in range(11, 17)]
        pasos += [paso(16 * n, dy=-6.0) for n in range(17, 27)]
        elegidos = seleccion.seleccionar_frames(pasos)
        self.assertEqual({dato["pasada"] for dato in elegidos}, {1, 2})
        for dato in elegidos:
            if dato["frame"] <= 160:
                self.assertEqual(dato["sentido"], "avance")
            else:
                self.assertEqual(dato["sentido"], "retroceso")
            self.assertFalse(160 < dato["frame"] < 256)

    def test_sin_movimiento_no_elige_nada(self):
        pasos = [paso(16 * n, dx=0.1, dy=0.1) for n in range(1, 21)]
        self.assertEqual(seleccion.seleccionar_frames(pasos), [])

    def test_un_paso_no_confiable_no_corta_la_fase(self):
        pasos = [paso(16 * n, dy=6.0) for n in range(1, 11)]
        pasos.append({"frame": 176, "confiable": False})
        pasos += [paso(16 * n, dy=6.0) for n in range(12, 22)]
        elegidos = seleccion.seleccionar_frames(pasos)
        self.assertEqual({dato["pasada"] for dato in elegidos}, {1})

    def test_plan_b_por_intervalo(self):
        elegidos = seleccion.seleccionar_por_intervalo(4303, 29.97, 2.0)
        self.assertEqual(len(elegidos), 72)
        self.assertEqual(elegidos[0]["frame"], 0)
        self.assertEqual(elegidos[-1]["frame"], 4260)
        self.assertEqual(elegidos[0]["sentido"], "intervalo fijo")
        self.assertIsNone(elegidos[0]["solape"])

if __name__ == "__main__":
    unittest.main()