import logging

import web

from mvc.compartido.seguridad import firmar
from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, error_formulario, formulario, render, validar_enlace
from ..models.seguimientos import aplicar_auditoria, detalle_auditoria, listar_auditoria

logger = logging.getLogger(__name__)
DICTAMENES_VALIDOS = ("Sin Novedad", "En Inspección", "Rescatado", "Falsa Alarma")


class AuditarSeguimiento:
    """Controlador RF18: supervisión de evidencias, alertas de maltrato y dictamen admin."""

    def GET(self, enlace: str = "") -> str:
        if enlace.startswith("mascota/"):
            id_mascota = validar_enlace(enlace.removeprefix("mascota/"))
            usuario = validar_sesion(["Publicador", "Admin"])
            filas = listar_auditoria(usuario, id_mascota=id_mascota)
            if not filas and usuario["rol"] == "Publicador":
                logger.info("Consulta sin resultados o sin propiedad para mascota en auditoría.")
            for fila in filas:
                fila["enlace"] = firmar(int(fila["id_seguimiento"]))
                fila["enlace_mascota"] = firmar(int(fila["id_mascota"]))
            return str(render.auditar_seguimiento(usuario["rol"], filas, "todos", True))

        if enlace:
            id_seguimiento = validar_enlace(enlace)
            usuario = validar_sesion(["Publicador", "Admin"])
            fila = detalle_auditoria(usuario, id_seguimiento)
            fila["enlace"] = enlace
            fila["enlace_mascota"] = firmar(int(fila["id_mascota"]))
            return str(render.auditar_detalle(usuario["rol"], fila, csrf()))

        usuario = validar_sesion(["Publicador", "Admin"])
        filtro = str(web.input(filtro="todos").get("filtro", "todos"))
        solo_alertas = filtro == "alertas"
        filas = listar_auditoria(usuario, solo_alertas=solo_alertas)
        for fila in filas:
            fila["enlace"] = firmar(int(fila["id_seguimiento"]))
            fila["enlace_mascota"] = firmar(int(fila["id_mascota"]))
        return str(render.auditar_seguimiento(usuario["rol"], filas, "alertas" if solo_alertas else "todos", False))

    def POST(self, enlace: str = "") -> None:
        if not enlace or enlace.startswith("mascota/"):
            denegar()
        id_seguimiento = validar_enlace(enlace)
        usuario = validar_sesion(["Publicador", "Admin"])
        datos = formulario()

        detalle_auditoria(usuario, id_seguimiento)

        if usuario["rol"] == "Publicador":
            if str(datos.get("accion", "")) != "activar_alerta":
                error_formulario("Acción no autorizada para el rol publicador.")
            aplicar_auditoria(usuario["id_usuario"], id_seguimiento, activar=True)
            raise web.seeother("/auditar_seguimiento/" + enlace)

        dictamen = str(datos.get("dictamen_admin", "")).strip()
        notas = str(datos.get("notas_auditoria", "")).strip()
        activar_alerta = datos.get("alerta_maltrato") == "si"
        suspender = datos.get("suspender_adoptante") == "si"

        if dictamen not in DICTAMENES_VALIDOS:
            error_formulario("Selecciona un dictamen de auditoría válido.")
        if len(notas) > 2000 or "\x00" in notas:
            error_formulario("Las notas de auditoría admiten hasta 2000 caracteres.")
        if (dictamen != "Sin Novedad" or suspender) and not notas:
            error_formulario("Debes registrar notas de auditoría al emitir un dictamen o suspender una cuenta.")

        aplicar_auditoria(
            usuario["id_usuario"],
            id_seguimiento,
            activar=activar_alerta,
            dictamen=dictamen,
            notas=notas,
            suspender_adoptante=suspender,
        )
        raise web.seeother("/auditar_seguimiento/" + enlace)
