import logging

import web

from mvc.compartido.seguridad import firmar
from mvc.compartido.sesion import validar_sesion
from .comun import (
    csrf,
    denegar,
    eliminar_foto_seguimiento,
    error_formulario,
    formulario,
    guardar_foto_seguimiento,
    render,
    validar_enlace,
)
from ..models.seguimientos import (
    adopciones_adoptante,
    registrar_reporte,
    verificar_adopcion_adoptante,
)

logger = logging.getLogger(__name__)


class SubirSeguimiento:
    """Controlador RF17: listado de adopciones del adoptante y carga de reporte mensual."""

    def GET(self, enlace: str = "") -> str:
        if not enlace:
            usuario = validar_sesion(["Adoptante"])
            adopciones = adopciones_adoptante(usuario["id_usuario"])
            tarjetas = [{**item, "enlace": firmar(item["id_mascota"])} for item in adopciones]
            return str(render.mis_adopciones(tarjetas))

        id_mascota = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante"])
        adopcion = verificar_adopcion_adoptante(usuario["id_usuario"], id_mascota)
        if not adopcion:
            denegar()
        return str(render.subir_seguimiento(adopcion["mascotas"]["nombre"], enlace, csrf()))

    def POST(self, enlace: str = "") -> None:
        if not enlace:
            denegar()
        id_mascota = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante"])
        datos = formulario({"foto_evidencia": {}})

        adopcion = verificar_adopcion_adoptante(usuario["id_usuario"], id_mascota)
        if not adopcion:
            denegar()

        comentario = str(datos.get("comentario", "")).strip()
        if not 10 <= len(comentario) <= 2000 or "\x00" in comentario:
            error_formulario("Describe el estado de salud y cuidados usando entre 10 y 2000 caracteres.")

        nombre_foto = guardar_foto_seguimiento(datos.get("foto_evidencia"))
        try:
            registrar_reporte(usuario["id_usuario"], id_mascota, nombre_foto, comentario)
        except Exception as error:
            eliminar_foto_seguimiento(nombre_foto)
            logger.error("Error 12 al registrar reporte de seguimiento (%s).", type(error).__name__)
            raise

        raise web.seeother("/subir_seguimiento")
