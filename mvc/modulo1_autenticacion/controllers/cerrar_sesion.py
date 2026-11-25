from __future__ import annotations

import logging

import web

from .comun import csrf_valido
from ..models import sesiones
from ..models.usuarios import revocar_token_auth

logger = logging.getLogger(__name__)


class CerrarSesion:
    def GET(self) -> None:
        raise web.seeother("/")

    def POST(self) -> None:
        sesion = web.ctx.session
        if not csrf_valido(web.input()):
            raise web.seeother("/")
        token = sesion.get("token")
        if token:
            sesiones.cerrar(token)
            revocar_token_auth(token)
        try:
            sesion.kill()
        except KeyError:
            pass
        logger.info("Sesión cerrada.")
        raise web.seeother("/login")
