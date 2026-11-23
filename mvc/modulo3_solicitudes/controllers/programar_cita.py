import logging
from datetime import date, time

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, error_formulario, formulario, render, validar_enlace
from ..models.citas import programar
from ..models.solicitudes import activa, detalle

logger = logging.getLogger(__name__)


class ProgramarCita:
    def GET(self, enlace: str) -> str:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Publicador"])
        fila = detalle(usuario, solicitud)
        if not activa(fila) or fila["estado_solicitud"] != "Aprobada":
            denegar()
        return render.programar_cita(fila["mascotas"]["nombre"], csrf())

    def POST(self, enlace: str) -> None:
        solicitud = validar_enlace(enlace)
        usuario = validar_sesion(["Publicador"])
        datos = formulario()
        lugar = datos.get("lugar", "").strip()
        try:
            fecha = date.fromisoformat(datos.get("fecha", ""))
            hora = time.fromisoformat(datos.get("hora", ""))
        except ValueError:
            logger.info("Error 05. Fecha u hora inválida.")
            error_formulario("Revisa la fecha y la hora de la cita.")
        if not 1 <= len(lugar) <= 250 or hora.tzinfo is not None:
            error_formulario("Indica la hora local y un lugar de hasta 250 caracteres.")
        programar(usuario["id_usuario"], solicitud, fecha.isoformat(), hora.isoformat(), lugar)
        raise web.seeother("/lista_solicitudes")
