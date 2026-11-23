import logging

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, error_formulario, formulario, render, validar_enlace
from ..models.mensajes import enviar, historial

logger = logging.getLogger(__name__)


class MensajeriaSolicitud:
    def GET(self, enlace: str) -> str:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante", "Publicador"])
        mensajes = historial(usuario["id_usuario"], solicitud)
        return render.mensajeria_solicitud(mensajes, csrf())

    def POST(self, enlace: str) -> None:
        solicitud = validar_enlace(enlace)
        datos = formulario()
        texto = datos.get("contenido", "").strip()
        if not 1 <= len(texto) <= 4000 or "\x00" in texto:
            error_formulario("Escribe un mensaje de entre 1 y 4000 caracteres.")
        usuario = validar_sesion(["Adoptante", "Publicador"])
        enviar(usuario["id_usuario"], solicitud, texto)
        raise web.seeother("/mensajeria_solicitud/" + enlace)
