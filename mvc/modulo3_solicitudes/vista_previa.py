import argparse
import logging

import web

from .controllers.estilos import Estilos
from .controllers.vista_previa import VistaPrevia

logger = logging.getLogger(__name__)

urls = (
    r"/modulo3/estilos\.css", "Estilos",
    "/", "VistaPrevia",
    "/lista_solicitudes", "VistaPrevia",
    "/cuestionario_aptitud/(demostracion)", "VistaPrevia",
    "/enviar_solicitud/(demostracion)", "VistaPrevia",
    "/cancelar_solicitud/(demostracion)", "VistaPrevia",
    "/evaluar_solicitud/(demostracion)", "VistaPrevia",
    "/programar_cita/(demostracion)", "VistaPrevia",
    "/mensajeria_solicitud/(demostracion)", "VistaPrevia",
)


def iniciar() -> None:
    argumentos = argparse.ArgumentParser(description="Vista previa local de AdoPetMyao, sin base de datos.")
    argumentos.add_argument("--puerto", type=int, default=8090)
    puerto = argumentos.parse_args().puerto
    if not 1024 <= puerto <= 65535:
        argumentos.error("El puerto debe estar entre 1024 y 65535.")
    logging.basicConfig(level=logging.INFO)
    web.config.debug = False
    aplicacion = web.application(urls, globals())
    print(f"Vista previa de AdoPetMyao: http://127.0.0.1:{puerto}", flush=True)
    print("Datos simulados. Sin acceso a Supabase. Para detener: Ctrl + C.", flush=True)
    try:
        web.httpserver.runsimple(aplicacion.wsgifunc(), ("127.0.0.1", puerto))
    except OSError:
        logger.error("Error 07. No se pudo abrir el puerto %s. Prueba otro con --puerto.", puerto)
        raise SystemExit(1) from None


if __name__ == "__main__":
    iniciar()
