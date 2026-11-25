from __future__ import annotations

import logging

import web

from mvc.compartido.sesion import consultar_sesion
from .comun import csrf, csrf_valido, render, sin_cache, tomar_aviso
from ..models import sesiones
from ..models.usuarios import ServicioNoDisponible, autenticar, buscar, revocar_token_auth

logger = logging.getLogger(__name__)

CREDENCIALES_INCORRECTAS = "Credenciales incorrectas, verifique sus datos"
CUENTA_PENDIENTE = "Tu registro está en revisión por el administrador. Podrás iniciar sesión cuando sea aprobado."
CUENTA_SUSPENDIDA = "Tu cuenta está suspendida y no puedes iniciar sesión. Contacta al administrador."


def nueva_sesion() -> None:
    """Cambia el identificador de la sesión de web.py (evita fijación de sesión)."""
    sesion = web.ctx.session
    try:
        del sesion.store[sesion.session_id]
    except KeyError:
        pass
    sesion.session_id = sesion._generate_session_id()


class Login:
    def GET(self) -> str:
        if consultar_sesion() is not None:
            raise web.seeother("/")
        sin_cache()
        return str(render.login("", "", tomar_aviso(), csrf()))

    def POST(self) -> str:
        entrada = web.input()
        correo = str(entrada.get("correo", "")).strip().lower()
        password = str(entrada.get("password", ""))
        sin_cache()
        if not csrf_valido(entrada):
            return str(render.login(correo, "El formulario caducó. Vuelve a intentarlo.", "", csrf()))
        if not correo or not password:
            return str(render.login(correo, "Escribe tu correo y tu contraseña.", "", csrf()))
        try:
            resultado = autenticar(correo, password)
            if resultado is None:
                return str(render.login(correo, CREDENCIALES_INCORRECTAS, "", csrf()))
            token, auth_id = resultado
            usuario = buscar(auth_id, correo)
            if usuario is None:
                logger.warning("Cuenta de Auth sin fila en usuarios.")
                revocar_token_auth(token)
                return str(render.login(correo, CREDENCIALES_INCORRECTAS, "", csrf()))
            if usuario["estado_cuenta"] == "Pendiente":
                revocar_token_auth(token)
                return str(render.login(correo, CUENTA_PENDIENTE, "", csrf()))
            if usuario["estado_cuenta"] == "Suspendido":
                revocar_token_auth(token)
                mensaje = CUENTA_SUSPENDIDA
                if usuario.get("motivo_suspension"):
                    mensaje += " Motivo: " + str(usuario["motivo_suspension"])
                return str(render.login(correo, mensaje, "", csrf()))
            sesiones.abrir(token, int(usuario["id_usuario"]))
        except ServicioNoDisponible:
            return str(render.login(correo, "No se pudo iniciar sesión en este momento. Intenta más tarde.", "", csrf()))
        except Exception as error:
            logger.error("Error 20 al abrir la sesión (%s).", type(error).__name__)
            return str(render.login(correo, "No se pudo iniciar sesión en este momento. Intenta más tarde.", "", csrf()))
        nueva_sesion()
        sesion = web.ctx.session
        sesion.token = token
        sesion.id_usuario = int(usuario["id_usuario"])
        sesion.rol = usuario["rol"]
        sesion.nombre = usuario["nombre_completo"]
        sesion.csrf = None
        logger.info("Inicio de sesión correcto (rol %s).", usuario["rol"])
        raise web.seeother("/")
