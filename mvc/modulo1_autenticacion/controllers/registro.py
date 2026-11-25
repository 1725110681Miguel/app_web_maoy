from __future__ import annotations

import logging
import re
from typing import Dict, List

import web

from mvc.compartido.sesion import consultar_sesion
from .comun import avisar, csrf, csrf_valido, render, sin_cache
from ..models.usuarios import CorreoDuplicado, PasswordRechazada, ServicioNoDisponible, registrar

logger = logging.getLogger(__name__)

CAMPOS = ("nombre_completo", "correo", "password", "telefono", "direccion", "rol")
ROLES = ("Adoptante", "Publicador")
CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
TELEFONO = re.compile(r"\+?[0-9][0-9 ()-]{6,18}[0-9]")


def validar(datos: Dict[str, str]) -> List[str]:
    errores: List[str] = []
    if any(not datos[campo] for campo in CAMPOS):
        errores.append("Completa todos los campos obligatorios.")
    if datos["nombre_completo"] and len(datos["nombre_completo"]) > 150:
        errores.append("El nombre completo admite máximo 150 caracteres.")
    if datos["correo"] and (len(datos["correo"]) > 100 or not CORREO.fullmatch(datos["correo"])):
        errores.append("Escribe un correo electrónico válido.")
    if datos["password"] and not 8 <= len(datos["password"]) <= 72:
        errores.append("La contraseña debe tener entre 8 y 72 caracteres.")
    if datos["telefono"] and not TELEFONO.fullmatch(datos["telefono"]):
        errores.append("Escribe un teléfono válido (solo números, de 8 a 20 caracteres).")
    if datos["rol"] and datos["rol"] not in ROLES:
        errores.append("Elige un tipo de cuenta válido.")
    return errores


class Registro:
    def GET(self) -> str:
        if consultar_sesion() is not None:
            raise web.seeother("/")
        sin_cache()
        return str(render.registro({}, [], csrf()))

    def POST(self) -> str:
        entrada = web.input()
        datos = {campo: str(entrada.get(campo, "")).strip() for campo in CAMPOS}
        datos["password"] = str(entrada.get("password", ""))
        datos["correo"] = datos["correo"].lower()
        sin_cache()
        if not csrf_valido(entrada):
            return str(render.registro(datos, ["El formulario caducó. Vuelve a enviarlo."], csrf()))
        errores = validar(datos)
        if errores:
            return str(render.registro(datos, errores, csrf()))
        try:
            estado = registrar(datos)
        except CorreoDuplicado:
            return str(render.registro(datos, ["Este correo ya está registrado. Inicia sesión o usa otro correo."], csrf()))
        except PasswordRechazada:
            return str(render.registro(datos, ["La contraseña es demasiado débil. Usa letras y números."], csrf()))
        except ServicioNoDisponible:
            return str(render.registro(datos, ["No se pudo crear la cuenta en este momento. Intenta más tarde."], csrf()))
        if estado == "Pendiente":
            avisar("Tu solicitud de registro como refugio fue enviada. Un administrador la revisará y podrás iniciar sesión cuando sea aprobada.")
        else:
            avisar("¡Tu cuenta fue creada! Ya puedes iniciar sesión.")
        raise web.seeother("/login")
