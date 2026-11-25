from __future__ import annotations

import hashlib
import logging
from typing import Optional, Sequence, TypedDict

import web

from mvc.compartido.conexion import obtener_cliente

logger = logging.getLogger(__name__)


class Usuario(TypedDict):
    id_usuario: int
    rol: str


def huella_token(token: str) -> str:
    """Huella SHA-256 del token JWT que se guarda en `sesiones_abiertas`.

    El JWT completo puede superar los 512 caracteres de la columna `token`,
    así que se guarda su huella (64 caracteres). Si alguien lee la tabla, no
    obtiene tokens utilizables.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def consultar_sesion(roles_permitidos: Optional[Sequence[str]] = None) -> Optional[Usuario]:
    """Devuelve el usuario si la sesión de web.py tiene un token vigente en
    Supabase Auth y registrado en `sesiones_abiertas`; si no, None."""
    token = web.ctx.session.get("token")
    if not token:
        return None
    try:
        cliente = obtener_cliente()
        cuenta = cliente.auth.get_user(token)
        filas = (
            cliente.table("sesiones_abiertas")
            .select("usuarios!inner(id_usuario,rol,correo,estado_cuenta)")
            .eq("token", huella_token(token))
            .limit(1)
            .execute().data
        )
        if filas and cuenta and cuenta.user and cuenta.user.email:
            usuario = filas[0]["usuarios"]
            if (
                usuario["estado_cuenta"] == "Activo"
                and (roles_permitidos is None or usuario["rol"] in roles_permitidos)
                and usuario["correo"].casefold() == cuenta.user.email.casefold()
            ):
                return Usuario(id_usuario=int(usuario["id_usuario"]), rol=usuario["rol"])
    except Exception as error:
        logger.warning("Error 03 al comprobar la sesión (%s).", type(error).__name__)
    return None


def validar_sesion(roles_permitidos: list[str]) -> Usuario:
    usuario = consultar_sesion(roles_permitidos)
    if usuario is None:
        raise web.seeother("/login")
    return usuario
