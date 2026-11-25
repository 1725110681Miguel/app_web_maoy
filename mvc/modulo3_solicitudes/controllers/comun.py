import hmac
import logging
import secrets
from pathlib import Path
from typing import Any

try:
    from typing import Never
except ImportError:  # Python < 3.11
    from typing_extensions import Never

import web

from mvc.compartido.seguridad import verificar

logger = logging.getLogger(__name__)
render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"), base="base")


def validar_enlace(valor: str) -> int:
    identificador = verificar(valor)
    if identificador is None:
        denegar()
    return identificador


def denegar() -> Never:
    raise web.notfound("Recurso no encontrado o acceso denegado")


def error_formulario(mensaje: str) -> Never:
    raise web.HTTPError("400 Bad Request", {"Content-Type": "text/plain; charset=utf-8"}, mensaje)


def csrf() -> str:
    sesion = web.ctx.session
    if not sesion.get("csrf"):
        sesion.csrf = secrets.token_hex(32)
    return sesion.csrf


def formulario() -> Any:
    datos = web.input()
    recibido = datos.get("csrf", "")
    esperado = web.ctx.session.get("csrf", "")
    if not esperado or not hmac.compare_digest(esperado.encode(), recibido.encode()):
        raise web.forbidden("El formulario caducó. Recarga la página.")
    return datos
