import logging
from pathlib import Path

import web

logger = logging.getLogger(__name__)
render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"))


class VistaPrevia:
    """Vista previa local del Módulo 5 con datos simulados sin conexión a Supabase."""

    def GET(self, enlace: str = "") -> str:
        if not enlace:
            cuentas = [
                {
                    "nombre_completo": "Refugio Patitas Felices A.C.",
                    "correo": "contacto@patitas.org",
                    "rol": "Publicador",
                    "estado_cuenta": "Pendiente",
                    "motivo_suspension": None,
                    "fecha_registro": "2026-11-24",
                    "enlace": "demostracion",
                },
                {
                    "nombre_completo": "María López",
                    "correo": "maria@ejemplo.org",
                    "rol": "Adoptante",
                    "estado_cuenta": "Activo",
                    "motivo_suspension": None,
                    "fecha_registro": "2026-10-15",
                    "enlace": "demostracion",
                },
            ]
            contenido = render.moderar_cuentas(cuentas, "Todos")
        else:
            cuenta = {
                "nombre_completo": "Refugio Patitas Felices A.C.",
                "correo": "contacto@patitas.org",
                "telefono": "5512345678",
                "direccion": "Av. Reforma 120, Col. Centro",
                "rol": "Publicador",
                "estado_cuenta": "Pendiente",
                "motivo_suspension": None,
                "fecha_registro": "2026-11-24T10:15:00",
            }
            contenido = render.detalle_cuenta(cuenta, "demostracion", "csrf-demo", False)

        web.header("Content-Type", "text/html; charset=utf-8")
        web.header("Cache-Control", "no-store")
        return str(render.base(contenido, True))
