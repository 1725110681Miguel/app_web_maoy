from __future__ import annotations

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
def csrf_sesion() -> str:
    """Token CSRF de la sesión, para el formulario de cerrar sesión del layout."""
    try:
        if getattr(web.ctx, "session", None) is not None:
            return csrf()
    except Exception:
        return ""
    return ""


render = web.template.render(
    str(Path(__file__).resolve().parents[1] / "views"),
    base="base",
    globals={"csrf_sesion": csrf_sesion},
)


def validar_enlace(valor: str) -> int:
    """Valida firma HMAC-SHA256 antes de consultar la base de datos."""
    identificador = verificar(valor)
    if identificador is None:
        denegar()
    return identificador


def denegar() -> Never:
    """Aborta con HTTP 404 ante firmas inválidas o recursos inexistentes."""
    raise web.notfound("Recurso no encontrado o acceso denegado")


def error_formulario(mensaje: str) -> Never:
    """Responde con HTTP 400 describiendo el error de validación."""
    raise web.HTTPError("400 Bad Request", {"Content-Type": "text/plain; charset=utf-8"}, mensaje)


def csrf() -> str:
    """Obtiene o genera el token anti-CSRF de la sesión actual."""
    sesion = web.ctx.session
    if not sesion.get("csrf"):
        sesion.csrf = secrets.token_hex(32)
    return str(sesion.csrf)


def formulario() -> Any:
    """Valida el token CSRF recibido en peticiones POST."""
    datos = web.input()
    recibido = str(datos.get("csrf", ""))
    esperado = str(web.ctx.session.get("csrf", ""))
    if not esperado or not hmac.compare_digest(esperado.encode(), recibido.encode()):
        raise web.forbidden("El formulario caducó. Recarga la página.")
    return datos
