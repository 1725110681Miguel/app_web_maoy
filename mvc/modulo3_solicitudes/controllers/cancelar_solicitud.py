import logging

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, formulario, render, validar_enlace
from ..models.solicitudes import activa, cambiar, detalle

logger = logging.getLogger(__name__)


class CancelarSolicitud:
    def GET(self, enlace: str) -> str:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante"])
        fila = detalle(usuario, solicitud)
        if not activa(fila):
            denegar()
        return render.cancelar_solicitud(fila["mascotas"]["nombre"], csrf())

    def POST(self, enlace: str) -> None:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante"])
        formulario()
        cambiar(usuario["id_usuario"], solicitud, "Cancelada")
        raise web.seeother("/lista_solicitudes")
