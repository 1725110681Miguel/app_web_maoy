import logging

from mvc.compartido.seguridad import firmar
from mvc.compartido.sesion import validar_sesion
from .comun import render
from ..models.notificaciones import recientes
from ..models.solicitudes import activa, consultar

logger = logging.getLogger(__name__)


class ListaSolicitudes:
    def GET(self) -> str:
        usuario = validar_sesion(["Adoptante", "Publicador"])
        filas = consultar(usuario)
        for fila in filas:
            fila["enlace"] = firmar(fila["id_solicitud"])
            fila["activa"] = activa(fila)
        return render.lista_solicitudes(usuario["rol"], filas, recientes(usuario["id_usuario"]))
