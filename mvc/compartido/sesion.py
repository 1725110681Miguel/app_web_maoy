import logging
from typing import TypedDict

import web

from mvc.compartido.conexion import obtener_cliente

logger = logging.getLogger(__name__)


class Usuario(TypedDict):
    id_usuario: int
    rol: str


def validar_sesion(roles_permitidos: list[str]) -> Usuario:
    token = web.ctx.session.get("token")
    if not token:
        raise web.seeother("/login")
    try:
        cliente = obtener_cliente()
        cuenta = cliente.auth.get_user(token)
        filas = (
            cliente.table("sesiones_abiertas")
            .select("usuarios!inner(id_usuario,rol,correo,estado_cuenta)")
            .eq("token", token)
            .limit(1)
            .execute().data
        )
        if filas and cuenta and cuenta.user and cuenta.user.email:
            usuario = filas[0]["usuarios"]
            if (
                usuario["estado_cuenta"] == "Activo"
                and usuario["rol"] in roles_permitidos
                and usuario["correo"].casefold() == cuenta.user.email.casefold()
            ):
                return Usuario(id_usuario=int(usuario["id_usuario"]), rol=usuario["rol"])
    except Exception as error:
        logger.warning("Error 03 al comprobar la sesión (%s).", type(error).__name__)
    raise web.seeother("/login")
