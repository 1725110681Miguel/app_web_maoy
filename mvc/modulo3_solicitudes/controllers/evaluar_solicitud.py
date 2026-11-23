import logging

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, error_formulario, formulario, render, validar_enlace
from ..models.solicitudes import activa, cambiar, detalle

logger = logging.getLogger(__name__)


class EvaluarSolicitud:
    def GET(self, enlace: str) -> str:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Publicador"])
        fila = detalle(usuario, solicitud)
        if not activa(fila) or fila["estado_solicitud"] != "Pendiente":
            denegar()
        return render.evaluar_solicitud(fila, csrf())

    def POST(self, enlace: str) -> None:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Publicador"])
        datos = formulario()
        estado = datos.get("estado", "")
        motivo = datos.get("motivo", "").strip()
        if estado not in ("Aprobada", "Rechazada") or (estado == "Rechazada" and not motivo):
            error_formulario("Elige una decisión y escribe el motivo si rechazas la solicitud.")
        if len(motivo) > 1500:
            error_formulario("El motivo admite hasta 1500 caracteres.")
        cambiar(usuario["id_usuario"], solicitud, estado, motivo)
        raise web.seeother("/lista_solicitudes")
