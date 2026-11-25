from __future__ import annotations

import hmac
import logging
import secrets
from pathlib import Path
from typing import Any

import web

logger = logging.getLogger(__name__)
render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"), base="base")


def csrf() -> str:
    """Token anti-CSRF guardado en la sesión (mismo que usa el módulo 3)."""
    sesion = web.ctx.session
    if not sesion.get("csrf"):
        sesion.csrf = secrets.token_hex(32)
    return sesion.csrf


def csrf_valido(datos: Any) -> bool:
    recibido = str(datos.get("csrf", ""))
    esperado = web.ctx.session.get("csrf", "") or ""
    return bool(esperado) and hmac.compare_digest(esperado.encode(), recibido.encode())


def avisar(mensaje: str) -> None:
    """Mensaje de una sola vez que se muestra en la siguiente página."""
    web.ctx.session.aviso = mensaje


def tomar_aviso() -> str:
    mensaje = web.ctx.session.get("aviso") or ""
    web.ctx.session.aviso = None
    return mensaje


def sin_cache() -> None:
    web.header("Content-Type", "text/html; charset=utf-8")
    web.header("Cache-Control", "no-store")
