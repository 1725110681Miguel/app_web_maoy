import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import web

os.environ.setdefault("SECRET_KEY", "clave-de-prueba-modulo4-segura-12345")

from mvc.compartido.seguridad import firmar
from mvc.modulo4_seguimiento.controllers import comun
from mvc.modulo4_seguimiento.controllers.auditar_seguimiento import AuditarSeguimiento
from mvc.modulo4_seguimiento.controllers.estilos import Estilos
from mvc.modulo4_seguimiento.controllers.notificar_seguimiento import NotificarSeguimiento, ejecutar_revision_diaria
from mvc.modulo4_seguimiento.controllers.subir_seguimiento import SubirSeguimiento
from mvc.modulo4_seguimiento.controllers.vista_previa import VistaPrevia


class DummySession(dict):
    def __getattr__(self, key: str):
        return self.get(key)

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class TestModulo4Seguimiento(unittest.TestCase):
    def setUp(self) -> None:
        self.session = DummySession(csrf="token-csrf-valido")
        web.ctx.session = self.session
        web.ctx.headers = []
        web.ctx.status = "200 OK"
        web.ctx.home = "http://127.0.0.1:8080"
        web.ctx.path = "/subir_seguimiento"

    def test_estilos_modulo4_contiene_paleta_oficial(self) -> None:
        css = Estilos().GET()
        self.assertIn("#154C79", css)
        self.assertIn("#268B86", css)
        self.assertIn("#F4A261", css)
        self.assertIn("#F8F9FA", css)

    def test_anti_idor_rechaza_id_crudo_sin_tocar_db(self) -> None:
        with patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.validar_sesion") as mock_sesion:
            with self.assertRaises(web.HTTPError):
                SubirSeguimiento().GET("123")
            self.assertIn("404", web.ctx.status)
            mock_sesion.assert_not_called()

        with patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.validar_sesion") as mock_sesion:
            with self.assertRaises(web.HTTPError):
                AuditarSeguimiento().GET("999:firma_invalida")
            self.assertIn("404", web.ctx.status)
            mock_sesion.assert_not_called()

    def test_anti_csrf_rechaza_token_invalido(self) -> None:
        enlace = firmar(10)
        with (
            patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.validar_sesion", return_value={"id_usuario": 5, "rol": "Adoptante"}),
            patch("web.input", return_value={"csrf": "token-incorrecto"}),
        ):
            with self.assertRaises(web.Forbidden):
                SubirSeguimiento().POST(enlace)

    def test_subir_seguimiento_guarda_imagen_y_llama_rpc(self) -> None:
        enlace = firmar(10)
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"contenido-imagen-valido"
        archivo = SimpleNamespace(filename="foto_luna.png", value=png_bytes)

        with tempfile.TemporaryDirectory() as tmpdir:
            carpeta_tmp = Path(tmpdir)
            with (
                patch.object(comun, "CARPETA_FOTOS_SEGUIMIENTO", carpeta_tmp),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.validar_sesion", return_value={"id_usuario": 5, "rol": "Adoptante"}),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.verificar_adopcion_adoptante", return_value={"id_solicitud": 1, "mascotas": {"nombre": "Luna"}}),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.registrar_reporte", return_value=77) as mock_rpc,
                patch("web.input", return_value={"csrf": "token-csrf-valido", "comentario": "Se encuentra muy sana y feliz en casa.", "foto_evidencia": archivo}),
            ):
                with self.assertRaises(web.SeeOther):
                    SubirSeguimiento().POST(enlace)

                archivos = list(carpeta_tmp.iterdir())
                self.assertEqual(len(archivos), 1)
                self.assertTrue(archivos[0].name.endswith("_foto_luna.png"))
                mock_rpc.assert_called_once()

    def test_subir_seguimiento_rechaza_extension_peligrosa_y_limpia_si_falla_rpc(self) -> None:
        enlace = firmar(10)
        archivo_malo = SimpleNamespace(filename="script.exe", value=b"MZ...")
        with (
            patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.validar_sesion", return_value={"id_usuario": 5, "rol": "Adoptante"}),
            patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.verificar_adopcion_adoptante", return_value={"id_solicitud": 1, "mascotas": {"nombre": "Luna"}}),
            patch("web.input", return_value={"csrf": "token-csrf-valido", "comentario": "Comentario suficientemente largo.", "foto_evidencia": archivo_malo}),
        ):
            with self.assertRaises(web.HTTPError):
                SubirSeguimiento().POST(enlace)

        # Limpieza física si falla el RPC
        jpg_bytes = b"\xff\xd8\xff\xe0" + b"datos-jpeg"
        archivo_jpg = SimpleNamespace(filename="luna.jpg", value=jpg_bytes)
        with tempfile.TemporaryDirectory() as tmpdir:
            carpeta_tmp = Path(tmpdir)
            with (
                patch.object(comun, "CARPETA_FOTOS_SEGUIMIENTO", carpeta_tmp),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.validar_sesion", return_value={"id_usuario": 5, "rol": "Adoptante"}),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.verificar_adopcion_adoptante", return_value={"id_solicitud": 1, "mascotas": {"nombre": "Luna"}}),
                patch("mvc.modulo4_seguimiento.controllers.subir_seguimiento.registrar_reporte", side_effect=RuntimeError("Fallo DB")),
                patch("web.input", return_value={"csrf": "token-csrf-valido", "comentario": "Comentario suficientemente largo.", "foto_evidencia": archivo_jpg}),
            ):
                with self.assertRaises(RuntimeError):
                    SubirSeguimiento().POST(enlace)
                self.assertEqual(list(carpeta_tmp.iterdir()), [])

    def test_auditar_seguimiento_publicador_y_admin(self) -> None:
        enlace = firmar(22)
        detalle_ficticio = {
            "id_seguimiento": 22,
            "id_mascota": 10,
            "id_adoptante": 5,
            "foto_evidencia": "123_luna.jpg",
            "comentario": "Todo bien",
            "fecha_reporte": "2026-11-25T10:00:00",
            "alerta_maltrato": False,
            "dictamen_admin": "Sin Novedad",
            "notas_auditoria": None,
            "mascotas": {"nombre": "Luna", "especie": "Perro", "raza": "Mestiza"},
            "usuarios": {"nombre_completo": "Carlos", "estado_cuenta": "Activo"},
        }
        with (
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.validar_sesion", return_value={"id_usuario": 3, "rol": "Publicador"}),
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.detalle_auditoria", return_value=detalle_ficticio),
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.aplicar_auditoria") as mock_aplicar,
            patch("web.input", return_value={"csrf": "token-csrf-valido", "accion": "activar_alerta"}),
        ):
            with self.assertRaises(web.SeeOther):
                AuditarSeguimiento().POST(enlace)
            mock_aplicar.assert_called_once_with(3, 22, activar=True)

        # Admin con dictamen sin notas debe fallar con 400
        with (
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.detalle_auditoria", return_value=detalle_ficticio),
            patch("web.input", return_value={"csrf": "token-csrf-valido", "dictamen_admin": "Rescatado", "notas_auditoria": ""}),
        ):
            with self.assertRaises(web.HTTPError):
                AuditarSeguimiento().POST(enlace)

        # Admin con dictamen y suspensión válidos
        with (
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.detalle_auditoria", return_value=detalle_ficticio),
            patch("mvc.modulo4_seguimiento.controllers.auditar_seguimiento.aplicar_auditoria") as mock_admin,
            patch("web.input", return_value={
                "csrf": "token-csrf-valido",
                "dictamen_admin": "Rescatado",
                "alerta_maltrato": "si",
                "notas_auditoria": "Rescate coordinado con refugio.",
                "suspender_adoptante": "si",
            }),
        ):
            with self.assertRaises(web.SeeOther):
                AuditarSeguimiento().POST(enlace)
            mock_admin.assert_called_once_with(
                1,
                22,
                activar=True,
                dictamen="Rescatado",
                notas="Rescate coordinado con refugio.",
                suspender_adoptante=True,
            )

    def test_notificar_seguimiento_get_post_y_cron(self) -> None:
        with (
            patch("mvc.modulo4_seguimiento.controllers.notificar_seguimiento.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo4_seguimiento.controllers.notificar_seguimiento.adopciones_atrasadas", return_value=[{
                "id_mascota": 10,
                "nombre_mascota": "Luna",
                "especie": "Perro",
                "adoptante": "Carlos",
                "correo_adoptante": "carlos@ejemplo.org",
                "ultima_actividad": "2026-10-01",
                "dias_sin_reporte": 55,
            }]),
            patch("web.input", return_value={"enviadas": "1"}),
        ):
            html = NotificarSeguimiento().GET()
            self.assertIn("Luna", html)
            self.assertIn("55 días", html)

        with (
            patch("mvc.modulo4_seguimiento.controllers.notificar_seguimiento.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo4_seguimiento.controllers.notificar_seguimiento.notificar_inactivos", return_value=2),
            patch("web.input", return_value={"csrf": "token-csrf-valido"}),
        ):
            with self.assertRaises(web.SeeOther):
                NotificarSeguimiento().POST()
            self.assertIn(("Location", "http://127.0.0.1:8080/notificar_seguimiento?enviadas=2"), web.ctx.headers)

        with patch("mvc.modulo4_seguimiento.controllers.notificar_seguimiento.notificar_inactivos", return_value=3):
            self.assertEqual(ejecutar_revision_diaria(), 3)

    def test_vista_previa_modulo4_renderiza_todas_las_pantallas(self) -> None:
        for ruta, enlace in [
            ("/subir_seguimiento", ""),
            ("/subir_seguimiento/demostracion", "demostracion"),
            ("/auditar_seguimiento", ""),
            ("/auditar_seguimiento/demostracion", "demostracion"),
            ("/notificar_seguimiento", ""),
        ]:
            web.ctx.path = ruta
            html = VistaPrevia().GET(enlace)
            self.assertIn("AdoPet", html)


if __name__ == "__main__":
    unittest.main()
