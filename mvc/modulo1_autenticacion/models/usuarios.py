from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError, AuthError

from mvc.compartido.conexion import obtener_cliente
from mvc.compartido.seguridad import cifrar_password

logger = logging.getLogger(__name__)

ESTADO_INICIAL = {"Adoptante": "Activo", "Publicador": "Pendiente"}


class CorreoDuplicado(Exception):
    """El correo ya pertenece a otra cuenta."""


class PasswordRechazada(Exception):
    """Supabase Auth rechazó la contraseña (demasiado débil)."""


class ServicioNoDisponible(Exception):
    """No se pudo completar la operación con Supabase."""


def correo_registrado(correo: str) -> bool:
    filas = (obtener_cliente().table("usuarios").select("id_usuario")
             .eq("correo", correo).limit(1).execute().data)
    return bool(filas)


def registrar(datos: Dict[str, str]) -> str:
    """RF01: crea la cuenta en Supabase Auth y la fila en `usuarios`.
    Devuelve el estado de la cuenta ('Activo' o 'Pendiente')."""
    try:
        cliente = obtener_cliente()
        if correo_registrado(datos["correo"]):
            raise CorreoDuplicado()
    except CorreoDuplicado:
        raise
    except Exception as error:
        logger.error("Error 11 al comprobar el correo (%s).", type(error).__name__)
        raise ServicioNoDisponible() from None

    try:
        respuesta = cliente.auth.admin.create_user({
            "email": datos["correo"],
            "password": datos["password"],
            "email_confirm": True,
            "user_metadata": {"nombre_completo": datos["nombre_completo"]},
        })
        auth_id = respuesta.user.id
    except AuthApiError as error:
        codigo = str(getattr(error, "code", "") or "")
        if codigo == "email_exists" or "already" in str(error).lower():
            raise CorreoDuplicado() from None
        if codigo == "weak_password" or "password" in str(error).lower():
            raise PasswordRechazada() from None
        logger.error("Error 12 al crear el usuario en Supabase Auth (%s).", codigo or type(error).__name__)
        raise ServicioNoDisponible() from None
    except Exception as error:
        logger.error("Error 13 al crear el usuario en Supabase Auth (%s).", type(error).__name__)
        raise ServicioNoDisponible() from None

    estado = ESTADO_INICIAL[datos["rol"]]
    try:
        cliente.table("usuarios").insert({
            "auth_id": auth_id,
            "nombre_completo": datos["nombre_completo"],
            "correo": datos["correo"],
            "password": cifrar_password(datos["password"]),
            "telefono": datos["telefono"],
            "direccion": datos["direccion"],
            "rol": datos["rol"],
            "estado_cuenta": estado,
        }).execute()
    except Exception as error:
        # Si falla la tabla, se deshace la cuenta de Auth para no dejarla huérfana.
        try:
            cliente.auth.admin.delete_user(auth_id)
        except Exception as error_borrado:
            logger.error("Error 14 al revertir el usuario de Auth (%s).", type(error_borrado).__name__)
        if isinstance(error, APIError) and error.code == "23505":
            raise CorreoDuplicado() from None
        logger.error("Error 15 al insertar en usuarios (%s).", getattr(error, "code", type(error).__name__))
        raise ServicioNoDisponible() from None
    logger.info("Usuario registrado con rol %s y estado %s.", datos["rol"], estado)
    return estado


def autenticar(correo: str, password: str) -> Optional[Tuple[str, str]]:
    """RF02: valida credenciales con Supabase Auth (sign_in_with_password).
    Devuelve (access_token, auth_id) o None si las credenciales son incorrectas."""
    try:
        # Cliente aparte: al iniciar sesión, el SDK cambia su encabezado de
        # autorización al JWT del usuario, y las tablas solo aceptan service_role.
        cliente = obtener_cliente()
        respuesta = cliente.auth.sign_in_with_password({"email": correo, "password": password})
    except AuthApiError as error:
        logger.info("Inicio de sesión rechazado (%s).", getattr(error, "code", "auth"))
        return None
    except AuthError as error:
        logger.info("Inicio de sesión rechazado (%s).", type(error).__name__)
        return None
    except Exception as error:
        logger.error("Error 16 al validar credenciales (%s).", type(error).__name__)
        raise ServicioNoDisponible() from None
    if not respuesta.session or not respuesta.user:
        return None
    return respuesta.session.access_token, respuesta.user.id


def buscar(auth_id: str, correo: str) -> Optional[Dict[str, Any]]:
    try:
        filas = (obtener_cliente().table("usuarios")
                 .select("id_usuario,nombre_completo,correo,rol,estado_cuenta,motivo_suspension")
                 .eq("auth_id", auth_id).limit(1).execute().data)
        if not filas:
            filas = (obtener_cliente().table("usuarios")
                     .select("id_usuario,nombre_completo,correo,rol,estado_cuenta,motivo_suspension")
                     .eq("correo", correo).limit(1).execute().data)
        return filas[0] if filas else None
    except Exception as error:
        logger.error("Error 17 al consultar el usuario (%s).", type(error).__name__)
        raise ServicioNoDisponible() from None


def revocar_token_auth(token: str) -> None:
    """Cierra la sesión del token en Supabase Auth (revoca su refresh token)."""
    try:
        obtener_cliente().auth.admin.sign_out(token)
    except Exception as error:
        logger.warning("Error 18 al cerrar la sesión en Supabase Auth (%s).", type(error).__name__)
