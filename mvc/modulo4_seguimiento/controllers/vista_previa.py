import logging
from pathlib import Path
from typing import Any

import web

logger = logging.getLogger(__name__)
render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"))


class VistaPrevia:
    """Vista previa local del Módulo 4 con datos simulados sin conexión a Supabase."""

    def GET(self, enlace: str = "") -> str:
        ruta = web.ctx.path.strip("/")
        pagina = ruta.split("/")[0] or "mis_adopciones"

        if pagina == "subir_seguimiento" and not enlace:
            contenido = render.mis_adopciones([
                {
                    "nombre": "Luna",
                    "especie": "Perro",
                    "raza": "Mestiza",
                    "foto": "mascota_default.webp",
                    "fecha_adopcion": "2026-10-10",
                    "ultimo_reporte": "2026-10-20",
                    "dias_sin_reporte": 36,
                    "atrasado": True,
                    "enlace": "demostracion",
                },
                {
                    "nombre": "Mishi",
                    "especie": "Gato",
                    "raza": "Atigrado",
                    "foto": "mascota_default.webp",
                    "fecha_adopcion": "2026-11-10",
                    "ultimo_reporte": "2026-11-20",
                    "dias_sin_reporte": 5,
                    "atrasado": False,
                    "enlace": "demostracion",
                },
            ])
        elif pagina == "subir_seguimiento":
            contenido = render.subir_seguimiento("Luna", "demostracion", "csrf-demo")
        elif pagina == "auditar_seguimiento" and not enlace:
            fila_ejemplo: dict[str, Any] = {
                "mascotas": {"nombre": "Luna", "especie": "Perro", "raza": "Mestiza"},
                "usuarios": {"nombre_completo": "Carlos Méndez", "estado_cuenta": "Activo"},
                "fecha_reporte": "2026-11-22",
                "alerta_maltrato": True,
                "dictamen_admin": "En Inspección",
                "enlace": "demostracion",
                "enlace_mascota": "demostracion",
            }
            contenido = render.auditar_seguimiento("Admin", [fila_ejemplo], "todos", False)
        elif pagina == "auditar_seguimiento":
            detalle_ejemplo: dict[str, Any] = {
                "mascotas": {"nombre": "Luna", "especie": "Perro", "raza": "Mestiza"},
                "usuarios": {"nombre_completo": "Carlos Méndez", "estado_cuenta": "Activo"},
                "foto_evidencia": "mascota_default.webp",
                "fecha_reporte": "2026-11-22T14:20:00",
                "comentario": "Ejemplo: se observa pérdida de peso en la fotografía enviada.",
                "alerta_maltrato": True,
                "dictamen_admin": "En Inspección",
                "notas_auditoria": "Visita programada con el refugio responsable.",
                "enlace": "demostracion",
            }
            contenido = render.auditar_detalle("Admin", detalle_ejemplo, "csrf-demo")
        elif pagina == "notificar_seguimiento":
            atrasados = [{
                "nombre_mascota": "Luna",
                "especie": "Perro",
                "adoptante": "Carlos Méndez",
                "correo_adoptante": "carlos@ejemplo.org",
                "ultima_actividad": "2026-10-18",
                "dias_sin_reporte": 38,
                "enlace_mascota": "demostracion",
            }]
            contenido = render.notificar_seguimiento(atrasados, "csrf-demo", "1")
        else:
            raise web.notfound()

        web.header("Content-Type", "text/html; charset=utf-8")
        web.header("Cache-Control", "no-store")
        return str(render.base(contenido, True))
