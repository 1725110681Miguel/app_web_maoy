import logging

import web

from mvc.compartido.seguridad import firmar
from mvc.compartido.sesion import validar_sesion
from .comun import csrf, formulario, render
from ..models.seguimientos import adopciones_atrasadas, notificar_inactivos

logger = logging.getLogger(__name__)


def ejecutar_revision_diaria() -> int:
    """Rutina automática (sin sesión web) para cron/temporizador diario de RF19."""
    try:
        total = notificar_inactivos(actor=None)
        logger.info("Revisión diaria RF19 completada: %s notificaciones enviadas.", total)
        return total
    except Exception as error:
        logger.error("Error 13 en revisión diaria RF19 (%s).", type(error).__name__)
        raise


class NotificarSeguimiento:
    """Controlador RF19: panel administrativo de retrasos >30 días y disparo manual."""

    def GET(self) -> str:
        validar_sesion(["Admin"])
        parametros = web.input(enviadas="")
        enviadas = str(parametros.get("enviadas", "")).strip()
        casos = adopciones_atrasadas(30)
        atrasados = [{**caso, "enlace_mascota": firmar(caso["id_mascota"])} for caso in casos]
        return str(render.notificar_seguimiento(atrasados, csrf(), enviadas))

    def POST(self) -> None:
        usuario = validar_sesion(["Admin"])
        formulario()
        total = notificar_inactivos(actor=usuario["id_usuario"])
        logger.info("Administrador %s ejecutó revisión RF19 (%s avisos).", usuario["id_usuario"], total)
        raise web.seeother(f"/notificar_seguimiento?enviadas={total}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    generadas = ejecutar_revision_diaria()
    print(f"Notificaciones generadas (>30 días sin seguimiento): {generadas}")
