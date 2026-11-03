import unittest
import cv2
import numpy as np
from src import calidad, config, mejora

REFERENCIA = {"brillo": 100.0, "contraste": 50.0, "nitidez_norm": 0.4}
SIN_PROBLEMAS = {"ajustes": [], "advertencias": []}

def imagen_gris(brillo=100.0, contraste=50.0, tamano=(120, 160), semilla=1):
    generador = np.random.default_rng(semilla)
    gris = generador.normal(brillo, contraste, tamano)
    gris = np.clip(gris, 0, 255).astype(np.uint8)
    return np.dstack([gris, gris, gris])

def imagen_color(bgr=(30, 45, 60), ruido=8.0, tamano=(120, 160), semilla=2):
    generador = np.random.default_rng(semilla)
    imagen = np.empty(tamano + (3,), dtype=np.float32)
    for canal, valor in enumerate(bgr):
        imagen[:, :, canal] = valor + generador.normal(0, ruido, tamano)
    return np.clip(imagen, 0, 255).astype(np.uint8)

class PruebasMejora(unittest.TestCase):

    def test_si_no_hay_ajustes_la_imagen_no_se_toca(self):
        imagen = imagen_gris()
        resultado, aplicados, diagnostico = mejora.mejorar_imagen(
            imagen, SIN_PROBLEMAS, REFERENCIA
        )
        self.assertEqual(aplicados, [])
        self.assertTrue(np.array_equal(imagen, resultado))   # exactamente los mismos píxeles
        self.assertEqual(diagnostico, SIN_PROBLEMAS)

    def test_imagen_oscura_se_aclara(self):
        oscura = (imagen_gris().astype(np.float32) * 0.7).astype(np.uint8)
        diagnostico = {"ajustes": ["oscura"], "advertencias": []}
        resultado, aplicados, final = mejora.mejorar_imagen(oscura, diagnostico, REFERENCIA)
        antes = calidad.medir_brillo_contraste(oscura)["brillo"]
        despues = calidad.medir_brillo_contraste(resultado)["brillo"]
        self.assertTrue(aplicados[0].startswith("brillo"))
        self.assertLess(abs(despues - 100.0), abs(antes - 100.0))   # quedó más cerca de lo normal
        self.assertEqual(final["ajustes"], [])                      # y ya no queda nada pendiente

    def test_el_tope_de_ganancia_limita_la_correccion(self):
        muy_oscura = (imagen_gris().astype(np.float32) * 0.3).astype(np.uint8)
        diagnostico = {"ajustes": ["oscura"], "advertencias": []}
        _, aplicados, _ = mejora.mejorar_imagen(muy_oscura, diagnostico, REFERENCIA)
        self.assertEqual(aplicados[0], f"brillo x{config.GANANCIA_MAXIMA:.2f}")

    def test_poco_contraste_se_estira(self):
        base = imagen_gris().astype(np.float32)
        media = base.mean()
        plana = np.clip(media + (base - media) * 0.65, 0, 255).astype(np.uint8)
        diagnostico = {"ajustes": ["poco_contraste"], "advertencias": []}
        resultado, aplicados, _ = mejora.mejorar_imagen(plana, diagnostico, REFERENCIA)
        antes = calidad.medir_brillo_contraste(plana)["contraste"]
        despues = calidad.medir_brillo_contraste(resultado)["contraste"]
        self.assertGreater(despues, antes)
        self.assertTrue(any(ajuste.startswith("contraste") for ajuste in aplicados))

    def test_poca_nitidez_se_realza(self):
        borrosa = cv2.GaussianBlur(imagen_gris(tamano=(216, 3840)), (0, 0), 1.5)
        diagnostico = {"ajustes": ["poca_nitidez"], "advertencias": []}
        resultado, aplicados, _ = mejora.mejorar_imagen(borrosa, diagnostico, REFERENCIA)
        antes = calidad.medir_nitidez(borrosa)["nitidez_norm"]
        despues = calidad.medir_nitidez(resultado)["nitidez_norm"]
        self.assertGreater(despues, antes)
        self.assertTrue(aplicados[0].startswith("nitidez"))

    def test_el_color_se_conserva_al_corregir_el_brillo(self):
        oscura = imagen_color()
        diagnostico = {"ajustes": ["oscura"], "advertencias": []}
        resultado, _, _ = mejora.mejorar_imagen(oscura, diagnostico, REFERENCIA)
        antes = cv2.cvtColor(oscura, cv2.COLOR_BGR2YCrCb).astype(np.int16)
        despues = cv2.cvtColor(resultado, cv2.COLOR_BGR2YCrCb).astype(np.int16)
        diferencia_cr = np.abs(antes[:, :, 1] - despues[:, :, 1]).mean()
        diferencia_cb = np.abs(antes[:, :, 2] - despues[:, :, 2]).mean()
        self.assertLess(diferencia_cr, 3.0)                          # el color casi no cambió
        self.assertLess(diferencia_cb, 3.0)
        self.assertGreater(despues[:, :, 0].mean(), antes[:, :, 0].mean())   # la luminosidad sí

if __name__ == "__main__":
    unittest.main()