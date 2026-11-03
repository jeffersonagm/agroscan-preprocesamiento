import unittest
from src import calidad

REFERENCIA = {"brillo": 100.0, "contraste": 50.0, "nitidez_norm": 0.4}

def medidas(**cambios):
    base = {
        "brillo": 100.0, "contraste": 50.0, "nitidez_norm": 0.4,
        "pct_quemado": 0.1, "pct_oscuro": 0.5,
        "desigualdad": 7.0, "esquinas_vs_centro": 97.0,
    }
    base.update(cambios)
    return base

class PruebasDiagnostico(unittest.TestCase):

    def test_imagen_normal_no_necesita_nada(self):
        resultado = calidad.diagnosticar_imagen(medidas(), REFERENCIA)
        self.assertEqual(resultado["ajustes"], [])
        self.assertEqual(resultado["advertencias"], [])

    def test_imagen_oscura(self):
        resultado = calidad.diagnosticar_imagen(medidas(brillo=50.0), REFERENCIA)
        self.assertIn("oscura", resultado["ajustes"])

    def test_imagen_clara(self):
        resultado = calidad.diagnosticar_imagen(medidas(brillo=140.0), REFERENCIA)
        self.assertIn("clara", resultado["ajustes"])

    def test_variacion_pequena_de_brillo_no_se_corrige(self):
        resultado = calidad.diagnosticar_imagen(medidas(brillo=85.0), REFERENCIA)
        self.assertEqual(resultado["ajustes"], [])

    def test_poco_contraste(self):
        resultado = calidad.diagnosticar_imagen(medidas(contraste=20.0), REFERENCIA)
        self.assertIn("poco_contraste", resultado["ajustes"])

    def test_poca_nitidez(self):
        resultado = calidad.diagnosticar_imagen(medidas(nitidez_norm=0.05), REFERENCIA)
        self.assertIn("poca_nitidez", resultado["ajustes"])

    def test_nitidez_algo_menor_no_se_marca(self):
        resultado = calidad.diagnosticar_imagen(medidas(nitidez_norm=0.2), REFERENCIA)
        self.assertEqual(resultado["ajustes"], [])

    def test_las_sombras_son_advertencias_y_no_ajustes(self):
        resultado = calidad.diagnosticar_imagen(
            medidas(desigualdad=30.0, esquinas_vs_centro=60.0), REFERENCIA
        )
        self.assertEqual(resultado["ajustes"], [])
        self.assertIn("iluminacion_desigual", resultado["advertencias"])
        self.assertIn("esquinas_oscuras", resultado["advertencias"])

    def test_zonas_quemadas_y_oscuras(self):
        resultado = calidad.diagnosticar_imagen(
            medidas(pct_quemado=6.0, pct_oscuro=6.0), REFERENCIA
        )
        self.assertIn("zonas_quemadas", resultado["advertencias"])
        self.assertIn("zonas_oscuras", resultado["advertencias"])

    def test_referencia_con_medianas(self):
        lista = [medidas(brillo=90.0), medidas(brillo=100.0), medidas(brillo=130.0)]
        referencia = calidad.calcular_referencia(lista)
        self.assertEqual(referencia["brillo"], 100.0)

if __name__ == "__main__":
    unittest.main()