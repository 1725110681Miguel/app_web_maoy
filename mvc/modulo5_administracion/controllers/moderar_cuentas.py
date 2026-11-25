import logging

import web

from mvc.compartido.seguridad import firmar
from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, error_formulario, formulario, render, validar_enlace
from ..models.cuentas import (
    ACCIONES_MODERACION,
    ESTADOS_CUENTA,
    listar_cuentas,
    moderar_cuenta,
    obtener_cuenta,
)

logger = logging.getLogger(__name__)


class ModerarCuentas:
    """Controlador RF20: aprobación de refugios y suspensión/reactivación de cuentas."""

    def GET(self, enlace: str = "") -> str:
        if enlace:
            id_objetivo = validar_enlace(enlace)
            usuario = validar_sesion(["Admin"])
            cuenta = obtener_cuenta(id_objetivo)
            es_propia = id_objetivo == usuario["id_usuario"]
            return str(render.detalle_cuenta(cuenta, enlace, csrf(), es_propia))

        validar_sesion(["Admin"])
        estado = str(web.input(estado="Todos").get("estado", "Todos"))
        filtro_estado = estado if estado in ESTADOS_CUENTA else "Todos"
        filas = listar_cuentas(None if filtro_estado == "Todos" else filtro_estado)
        cuentas = [{**fila, "enlace": firmar(int(fila["id_usuario"]))} for fila in filas]
        return str(render.moderar_cuentas(cuentas, filtro_estado))

    def POST(self, enlace: str = "") -> None:
        if not enlace:
            denegar()
        id_objetivo = validar_enlace(enlace)
        usuario = validar_sesion(["Admin"])
        datos = formulario()

        if id_objetivo == usuario["id_usuario"]:
            logger.warning("Error 18: administrador %s intentó moderar su propia cuenta.", usuario["id_usuario"])
            error_formulario("No puedes suspender ni modificar tu propia cuenta de administrador.")

        cuenta = obtener_cuenta(id_objetivo)
        if cuenta["rol"] == "Admin":
            error_formulario("No se permite moderar cuentas administrativas desde este panel.")

        accion = str(datos.get("accion", "")).strip()
        motivo = str(datos.get("motivo", "")).strip()

        if accion not in ACCIONES_MODERACION:
            error_formulario("Selecciona una acción de moderación válida.")
        if accion in ("Rechazar", "Suspender") and not motivo:
            error_formulario("Debes escribir el motivo obligatorio para rechazar o suspender la cuenta.")
        if len(motivo) > 1500 or "\x00" in motivo:
            error_formulario("El motivo admite hasta 1500 caracteres.")

        moderar_cuenta(usuario["id_usuario"], id_objetivo, accion, motivo)
        logger.info(
            "Administrador %s ejecutó acción '%s' sobre cuenta %s.",
            usuario["id_usuario"],
            accion,
            id_objetivo,
        )
        raise web.seeother("/moderar_cuentas/" + enlace)
