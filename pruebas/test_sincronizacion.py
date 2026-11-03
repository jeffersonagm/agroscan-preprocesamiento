import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import requests
from src import config, sincronizacion

class RespuestaFalsa:

    def __init__(self, codigo, datos=None):
        self.status_code = codigo
        self._datos = datos or {}

    def json(self):
        return self._datos


def post_correcto(url, files=None, data=None, timeout=None):
    nombre, archivo, tipo = files["archivo"]
    huella = hashlib.sha256(archivo.read()).hexdigest()
    return RespuestaFalsa(201, {"sha256": huella})

class PruebasSincronizacion(unittest.TestCase):

    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        raiz = Path(temporal.name)
        self.finales = raiz / "finales"
        self.finales.mkdir()
        self.estado = raiz / "estado.json"
        for nombre in ("a.jpg", "b.jpg", "c.jpg"):
            (self.finales / nombre).write_bytes(f"contenido de {nombre}".encode("utf-8"))
        parche_dormir = patch("src.sincronizacion.time.sleep")
        parche_dormir.start()
        self.addCleanup(parche_dormir.stop)
        parche_get = patch("src.sincronizacion.requests.get")
        self.mock_get = parche_get.start()
        self.addCleanup(parche_get.stop)
        parche_post = patch("src.sincronizacion.requests.post")
        self.mock_post = parche_post.start()
        self.addCleanup(parche_post.stop)
        self.mock_get.return_value = RespuestaFalsa(200, {"estado": "ok"})
        self.mock_post.side_effect = post_correcto

    def sincronizar(self):
        return sincronizacion.sincronizar(
            self.finales, "http://servidor.falso", "mision-prueba", self.estado
        )

    def test_envia_todo_cuando_hay_conexion(self):
        resultado = self.sincronizar()
        self.assertEqual(
            resultado, {"enviadas": 3, "pendientes": 0, "con_error": 0, "sin_conexion": False}
        )
        self.assertEqual(self.mock_post.call_count, 3)

    def test_la_segunda_ejecucion_no_reenvia_nada(self):
        self.sincronizar()
        self.sincronizar()
        self.assertEqual(self.mock_post.call_count, 3)    # solo las 3 del primer envío

    def test_sin_conexion_deja_todo_pendiente(self):
        self.mock_get.side_effect = requests.exceptions.ConnectionError()
        resultado = self.sincronizar()
        self.assertEqual(
            resultado, {"enviadas": 0, "pendientes": 3, "con_error": 0, "sin_conexion": True}
        )
        self.mock_post.assert_not_called()

    def test_si_el_servidor_se_cae_a_mitad_se_reanuda_solo_lo_que_falta(self):
        llamadas = {"cantidad": 0}

        def post_que_se_cae(url, files=None, data=None, timeout=None):
            llamadas["cantidad"] += 1
            if llamadas["cantidad"] == 1:
                return post_correcto(url, files=files, data=data, timeout=timeout)
            raise requests.exceptions.ConnectionError()
        self.mock_post.side_effect = post_que_se_cae
        primero = self.sincronizar()
        self.assertEqual(
            primero, {"enviadas": 1, "pendientes": 2, "con_error": 0, "sin_conexion": True}
        )
        self.assertEqual(self.mock_post.call_count, 1 + config.INTENTOS_POR_IMAGEN)
        self.mock_post.reset_mock()
        self.mock_post.side_effect = post_correcto
        segundo = self.sincronizar()
        self.assertEqual(segundo["enviadas"], 3)
        self.assertEqual(self.mock_post.call_count, 2)

    def test_el_rechazo_de_una_imagen_no_detiene_las_demas(self):
        def post_que_rechaza_b(url, files=None, data=None, timeout=None):
            if files["archivo"][0] == "b.jpg":
                return RespuestaFalsa(500)
            return post_correcto(url, files=files, data=data, timeout=timeout)
        self.mock_post.side_effect = post_que_rechaza_b
        resultado = self.sincronizar()
        self.assertEqual(
            resultado, {"enviadas": 2, "pendientes": 0, "con_error": 1, "sin_conexion": False}
        )

    def test_una_huella_distinta_se_considera_rechazo(self):
        self.mock_post.side_effect = None
        self.mock_post.return_value = RespuestaFalsa(201, {"sha256": "0" * 64})
        resultado = self.sincronizar()
        self.assertEqual(resultado["enviadas"], 0)
        self.assertEqual(resultado["con_error"], 3)

    def test_una_imagen_modificada_se_vuelve_a_enviar(self):
        self.sincronizar()
        (self.finales / "a.jpg").write_bytes(b"contenido distinto")   # la imagen cambia
        resultado = self.sincronizar()
        self.assertEqual(resultado["enviadas"], 3)
        self.assertEqual(self.mock_post.call_count, 4)    # 3 del primer envío y 1 de la modificada

    def test_el_estado_queda_guardado_en_disco(self):
        self.sincronizar()
        estado = json.loads(self.estado.read_text(encoding="utf-8"))
        for registro in estado["imagenes"].values():
            self.assertEqual(registro["estado"], "enviada")
            self.assertEqual(len(registro["huella"]), 64)

if __name__ == "__main__":
    unittest.main()