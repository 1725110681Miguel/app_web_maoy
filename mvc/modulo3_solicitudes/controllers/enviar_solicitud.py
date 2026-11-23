import logging
from typing import Any

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, formulario, render, validar_enlace
from ..models.solicitudes import enviar, mascota_disponible

logger = logging.getLogger(__name__)


def borrador(enlace: str) -> dict[str, Any]:
    mascota = validar_enlace(enlace)
    usuario = validar_sesion(["Adoptante"])
    datos = web.ctx.session.get("borrador")
    if not datos or datos["usuario"] != usuario["id_usuario"] or datos["mascota"] != mascota:
        raise web.seeother("/cuestionario_aptitud/" + enlace)
    return datos


class EnviarSolicitud:
    def GET(self, enlace: str) -> str:
        datos = borrador(enlace)
        ficha = mascota_disponible(datos["mascota"])
        if not ficha:
            denegar()
        return render.enviar_solicitud(ficha["nombre"], datos["respuestas"], csrf())

    def POST(self, enlace: str) -> None:
        datos = borrador(enlace)
        formulario()
        enviar(datos["usuario"], datos["mascota"], datos["respuestas"])
        web.ctx.session.borrador = None
        raise web.seeother("/lista_solicitudes")
