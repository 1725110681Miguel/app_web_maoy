from __future__ import annotations

import logging

from mvc.compartido.conexion import obtener_cliente
from mvc.compartido.sesion import huella_token

logger = logging.getLogger(__name__)


def abrir(token: str, id_usuario: int) -> None:
    """RF02: registra el token (su huella SHA-256) en `sesiones_abiertas`."""
    obtener_cliente().table("sesiones_abiertas").insert(
        {"token": huella_token(token), "id_usuario": id_usuario}
    ).execute()


def cerrar(token: str) -> None:
    """RF03: elimina el token de `sesiones_abiertas`."""
    try:
        obtener_cliente().table("sesiones_abiertas").delete().eq("token", huella_token(token)).execute()
    except Exception as error:
        logger.error("Error 19 al eliminar la sesión abierta (%s).", type(error).__name__)
