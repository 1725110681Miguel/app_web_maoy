import logging
from pathlib import Path
from typing import Any

import web

logger = logging.getLogger(__name__)
render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"))


class VistaPrevia:
    def GET(self, enlace: str = "") -> str:
        pagina = web.ctx.path.strip("/").split("/")[0] or "lista_solicitudes"
        nombre = "Mascota de demostración"
        respuestas = {
            "tipo_vivienda": "Departamento",
            "tiene_patio": False,
            "familia_de_acuerdo": True,
            "compromiso_gastos": True,
            "motivo_adopcion": "Ejemplo: ofrecer un hogar, compañía y cuidados constantes.",
        }
        fila = {
            **respuestas,
            "mascotas": {"nombre": nombre},
            "fecha_solicitud": "2026-11-25",
            "estado_solicitud": "Pendiente",
            "activa": True,
            "enlace": "demostracion",
        }
        ejemplos: dict[str, tuple[Any, ...]] = {
            "cuestionario_aptitud": (nombre, "demostracion"),
            "enviar_solicitud": (nombre, respuestas, "demostracion"),
            "lista_solicitudes": (
                "Adoptante", [fila],
                [{"mensaje": "Aviso de ejemplo: tu solicitud está pendiente de revisión."}],
            ),
            "cancelar_solicitud": (nombre, "demostracion"),
            "evaluar_solicitud": (fila, "demostracion"),
            "programar_cita": (nombre, "demostracion"),
            "mensajeria_solicitud": ([
                {"propio": False, "contenido": "Mensaje de ejemplo: gracias por tu interés en adoptar.",
                 "fecha_envio": "2026-11-25 09:30", "leido": True},
                {"propio": True, "contenido": "Respuesta de ejemplo: me gustaría conocer los siguientes pasos.",
                 "fecha_envio": "2026-11-25 09:35", "leido": False},
            ], "demostracion"),
        }
        if pagina not in ejemplos:
            raise web.notfound()
        contenido = getattr(render, pagina)(*ejemplos[pagina])
        web.header("Content-Type", "text/html; charset=utf-8")
        web.header("Cache-Control", "no-store")
        return str(render.base(contenido, True))
