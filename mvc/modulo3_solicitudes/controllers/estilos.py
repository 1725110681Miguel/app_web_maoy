import logging
from pathlib import Path

import web

logger = logging.getLogger(__name__)
ARCHIVO = Path(__file__).resolve().parents[1] / "static/css/solicitudes.css"


class Estilos:
    def GET(self) -> str:
        try:
            contenido = ARCHIVO.read_text(encoding="utf-8")
        except OSError as error:
            logger.error("Error 06 al cargar los estilos (%s).", type(error).__name__)
            raise web.notfound("No se pudo cargar el diseño del módulo.") from None
        web.header("Content-Type", "text/css; charset=utf-8")
        web.header("Cache-Control", "no-cache")
        web.header("X-Content-Type-Options", "nosniff")
        return contenido
