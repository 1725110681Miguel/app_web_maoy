import argparse
import logging

import web

from .controllers.estilos import Estilos
from .controllers.vista_previa import VistaPrevia

logger = logging.getLogger(__name__)

urls = (
    r"/modulo4/estilos\.css", "Estilos",
    "/", "VistaPrevia",
    "/subir_seguimiento", "VistaPrevia",
    "/subir_seguimiento/(demostracion)", "VistaPrevia",
    "/auditar_seguimiento", "VistaPrevia",
    "/auditar_seguimiento/(demostracion)", "VistaPrevia",
    "/notificar_seguimiento", "VistaPrevia",
)


def iniciar() -> None:
    argumentos = argparse.ArgumentParser(description="Vista previa local del Módulo 4 de AdoPetMyao.")
    argumentos.add_argument("--puerto", type=int, default=8091)
    puerto = argumentos.parse_args().puerto
    if not 1024 <= puerto <= 65535:
        argumentos.error("El puerto debe estar entre 1024 y 65535.")
    logging.basicConfig(level=logging.INFO)
    web.config.debug = False
    aplicacion = web.application(urls, globals())
    print(f"Vista previa Módulo 4: http://127.0.0.1:{puerto}/subir_seguimiento", flush=True)
    print("Datos simulados. Sin conexión a Supabase. Para detener: Ctrl + C.", flush=True)
    try:
        web.httpserver.runsimple(aplicacion.wsgifunc(), ("127.0.0.1", puerto))
    except OSError:
        logger.error("Error 14. No se pudo abrir el puerto %s.", puerto)
        raise SystemExit(1) from None


if __name__ == "__main__":
    iniciar()
