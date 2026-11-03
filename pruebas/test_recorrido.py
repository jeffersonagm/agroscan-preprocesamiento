import unittest
from src import config, recorrido

def paso(dx=0.0, dy=0.0, confiable=True):
    if not confiable:
        return {"frame": 16, "confiable": False}
    return {"frame": 16, "confiable": True, "dx": dx, "dy": dy, "angulo": 0.0, "puntos": 500}

class PruebasClasificacion(unittest.TestCase):

    def test_avance(self):
        self.assertEqual(recorrido.clasificar_paso(paso(dy=6.0)), "avance")

    def test_retroceso(self):
        self.assertEqual(recorrido.clasificar_paso(paso(dy=-6.0)), "retroceso")

    def test_lateral(self):
        self.assertEqual(recorrido.clasificar_paso(paso(dx=3.0, dy=0.5)), "lateral")

    def test_quieto(self):
        self.assertEqual(recorrido.clasificar_paso(paso(dx=0.1, dy=0.1)), "quieto")

    def test_no_confiable(self):
        self.assertEqual(recorrido.clasificar_paso(paso(confiable=False)), "no confiable")

    def test_el_umbral_vertical_cuenta_como_avance(self):
        self.assertEqual(recorrido.clasificar_paso(paso(dy=config.UMBRAL_VERTICAL)), "avance")

if __name__ == "__main__":
    unittest.main()