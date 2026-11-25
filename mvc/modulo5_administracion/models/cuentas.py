from __future__ import annotations

import logging
from typing import Any, TypedDict

import web
from postgrest.exceptions import APIError

from mvc.compartido.conexion import obtener_cliente

logger = logging.getLogger(__name__)

CAMPOS_CUENTA = (
    "id_usuario,nombre_completo,correo,telefono,direccion,"
    "rol,estado_cuenta,motivo_suspension,fecha_registro"
)
ESTADOS_CUENTA = ("Pendiente", "Activo", "Suspendido")
ACCIONES_MODERACION = ("Aprobar", "Rechazar", "Suspender", "Reactivar")
# La RPC en Supabase recibe estados (Activo/Pendiente/Suspendido), no los nombres de botón.
ACCION_A_ESTADO = {
    "Aprobar": "Activo",
    "Rechazar": "Suspendido",
    "Suspender": "Suspendido",
    "Reactivar": "Activo",
}


class CuentaUsuario(TypedDict):
    id_usuario: int
    nombre_completo: str
    correo: str
    telefono: str
    direccion: str
    rol: str
    estado_cuenta: str
    motivo_suspension: str | None
    fecha_registro: str


def ejecutar(nombre: str, parametros: dict[str, Any]) -> Any:
    """Ejecuta una función almacenada RPC de Supabase traduciendo errores de negocio."""
    try:
        return obtener_cliente().rpc(nombre, parametros).execute().data
    except APIError as error:
        if error.code == "P0001":
            raise web.HTTPError("409 Conflict", {"Content-Type": "text/plain; charset=utf-8"}, error.message)
        logger.error("Error 16 en RPC %s (%s).", nombre, error.code)
        raise web.internalerror("No se pudo completar la operación administrativa.") from None


def listar_cuentas(estado: str | None = None) -> list[CuentaUsuario]:
    """Consulta las cuentas de usuarios y refugios con filtro opcional por estado."""
    cliente = obtener_cliente()
    filas: list[CuentaUsuario] = []
    while True:
        consulta = cliente.table("usuarios").select(CAMPOS_CUENTA)
        if estado in ESTADOS_CUENTA:
            consulta = consulta.eq("estado_cuenta", estado)
        consulta = consulta.order("fecha_registro", desc=True).order("id_usuario", desc=True)
        pagina = consulta.range(len(filas), len(filas) + 199).execute().data
        filas.extend(pagina)
        if not pagina:
            return filas


def obtener_cuenta(id_usuario: int) -> CuentaUsuario:
    """Obtiene el expediente de una cuenta específica o aborta con HTTP 404."""
    filas = (
        obtener_cliente()
        .table("usuarios")
        .select(CAMPOS_CUENTA)
        .eq("id_usuario", id_usuario)
        .limit(1)
        .execute()
        .data
    )
    if not filas:
        raise web.notfound("Recurso no encontrado o acceso denegado")
    return filas[0]


def moderar_cuenta(admin_id: int, objetivo_id: int, accion: str, motivo: str = "") -> None:
    """Aplica el dictamen administrativo y revoca sesiones si corresponde."""
    ejecutar(
        "maow_moderar_cuenta",
        {
            "actor": admin_id,
            "usuario": objetivo_id,
            "nuevo_estado": ACCION_A_ESTADO[accion],
            "motivo": motivo or None,
        },
    )
