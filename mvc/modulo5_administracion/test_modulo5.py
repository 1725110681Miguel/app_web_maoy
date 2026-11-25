import os
import unittest
from unittest.mock import patch

import web

os.environ.setdefault("SECRET_KEY", "clave-de-prueba-modulo5-segura-12345")

from mvc.compartido.seguridad import firmar
from mvc.modulo5_administracion.controllers.estilos import Estilos
from mvc.modulo5_administracion.controllers.moderar_cuentas import ModerarCuentas
from mvc.modulo5_administracion.controllers.vista_previa import VistaPrevia


class DummySession(dict):
    def __getattr__(self, key: str):
        return self.get(key)

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class TestModulo5Administracion(unittest.TestCase):
    def setUp(self) -> None:
        self.session = DummySession(csrf="token-csrf-admin")
        web.ctx.session = self.session
        web.ctx.headers = []
        web.ctx.status = "200 OK"
        web.ctx.home = "http://127.0.0.1:8080"
        web.ctx.path = "/moderar_cuentas"

    def test_estilos_modulo5_contiene_paleta_oficial(self) -> None:
        css = Estilos().GET()
        self.assertIn("#154C79", css)
        self.assertIn("#268B86", css)
        self.assertIn("#F4A261", css)
        self.assertIn("#F8F9FA", css)

    def test_anti_idor_rechaza_id_usuario_no_firmado(self) -> None:
        with patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion") as mock_sesion:
            with self.assertRaises(web.HTTPError):
                ModerarCuentas().GET("42")
            self.assertIn("404", web.ctx.status)
            mock_sesion.assert_not_called()

    def test_anti_csrf_rechaza_post_sin_token_valido(self) -> None:
        enlace = firmar(42)
        with (
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("web.input", return_value={"csrf": "invalido"}),
        ):
            with self.assertRaises(web.Forbidden):
                ModerarCuentas().POST(enlace)

    def test_admin_no_puede_suspender_su_propia_cuenta(self) -> None:
        enlace_propio = firmar(1)
        with (
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("web.input", return_value={"csrf": "token-csrf-admin", "accion": "Suspender", "motivo": "Prueba"}),
        ):
            with self.assertRaises(web.HTTPError):
                ModerarCuentas().POST(enlace_propio)
            self.assertIn("400", web.ctx.status)

    def test_rechazar_o_suspender_exige_motivo_obligatorio(self) -> None:
        enlace = firmar(15)
        cuenta_pendiente = {
            "id_usuario": 15,
            "nombre_completo": "Refugio Sol",
            "correo": "sol@refugio.org",
            "telefono": "5555555555",
            "direccion": "Calle 1",
            "rol": "Publicador",
            "estado_cuenta": "Pendiente",
            "motivo_suspension": None,
            "fecha_registro": "2026-11-24T12:00:00",
        }
        with (
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.obtener_cuenta", return_value=cuenta_pendiente),
            patch("web.input", return_value={"csrf": "token-csrf-admin", "accion": "Rechazar", "motivo": "   "}),
        ):
            with self.assertRaises(web.HTTPError):
                ModerarCuentas().POST(enlace)

    def test_aprobar_y_suspender_cuenta_ejecuta_rpc(self) -> None:
        enlace = firmar(15)
        cuenta_pendiente = {
            "id_usuario": 15,
            "nombre_completo": "Refugio Sol",
            "correo": "sol@refugio.org",
            "telefono": "5555555555",
            "direccion": "Calle 1",
            "rol": "Publicador",
            "estado_cuenta": "Pendiente",
            "motivo_suspension": None,
            "fecha_registro": "2026-11-24T12:00:00",
        }
        with (
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.obtener_cuenta", return_value=cuenta_pendiente),
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.moderar_cuenta") as mock_rpc,
            patch("web.input", return_value={"csrf": "token-csrf-admin", "accion": "Aprobar", "motivo": ""}),
        ):
            with self.assertRaises(web.SeeOther):
                ModerarCuentas().POST(enlace)
            mock_rpc.assert_called_once_with(1, 15, "Aprobar", "")

    def test_listado_filtra_por_estado_y_firma_enlaces(self) -> None:
        cuentas = [{
            "id_usuario": 15,
            "nombre_completo": "Refugio Sol",
            "correo": "sol@refugio.org",
            "telefono": "5555555555",
            "direccion": "Calle 1",
            "rol": "Publicador",
            "estado_cuenta": "Pendiente",
            "motivo_suspension": None,
            "fecha_registro": "2026-11-24T12:00:00",
        }]
        with (
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.validar_sesion", return_value={"id_usuario": 1, "rol": "Admin"}),
            patch("mvc.modulo5_administracion.controllers.moderar_cuentas.listar_cuentas", return_value=cuentas) as mock_listar,
            patch("web.input", return_value={"estado": "Pendiente"}),
        ):
            html = ModerarCuentas().GET()
            mock_listar.assert_called_once_with("Pendiente")
            self.assertIn(firmar(15), html)
            self.assertIn("Refugio Sol", html)

    def test_vista_previa_modulo5_renderiza_listado_y_detalle(self) -> None:
        for enlace in ("", "demostracion"):
            html = VistaPrevia().GET(enlace)
            self.assertIn("AdoPet", html)


if __name__ == "__main__":
    unittest.main()
