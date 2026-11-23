import logging
from typing import Any

import web
from postgrest.exceptions import APIError

from mvc.compartido.conexion import obtener_cliente
from mvc.compartido.sesion import Usuario

logger = logging.getLogger(__name__)
CAMPOS = "*,mascotas!inner(nombre,id_publicador,estado_adopcion)"


def mascota_disponible(identificador: int) -> dict[str, Any] | None:
    filas = (obtener_cliente().table("mascotas").select("nombre")
             .eq("id_mascota", identificador).eq("estado_adopcion", "Disponible").limit(1).execute().data)
    return filas[0] if filas else None


def consultar(usuario: Usuario, identificador: int | None = None) -> list[dict[str, Any]]:
    cliente = obtener_cliente()
    campo = "id_adoptante" if usuario["rol"] == "Adoptante" else "mascotas.id_publicador"
    filas: list[dict[str, Any]] = []
    while True:
        consulta = cliente.table("solicitudes").select(CAMPOS).eq(campo, usuario["id_usuario"])
        if identificador is not None:
            consulta = consulta.eq("id_solicitud", identificador)
        consulta = consulta.order("fecha_solicitud", desc=True).order("id_solicitud", desc=True)
        pagina = consulta.range(len(filas), len(filas) + 199).execute().data
        filas.extend(pagina)
        if not pagina or identificador is not None:
            return filas


def detalle(usuario: Usuario, identificador: int) -> dict[str, Any]:
    filas = consultar(usuario, identificador)
    if not filas:
        raise web.notfound("Recurso no encontrado o acceso denegado")
    return filas[0]


def activa(fila: dict[str, Any]) -> bool:
    return fila["estado_solicitud"] in ("Pendiente", "Aprobada") and fila["mascotas"]["estado_adopcion"] != "Adoptada"


def ejecutar(nombre: str, parametros: dict[str, Any]) -> Any:
    try:
        return obtener_cliente().rpc(nombre, parametros).execute().data
    except APIError as error:
        if error.code == "P0001":
            raise web.HTTPError("409 Conflict", {"Content-Type": "text/plain; charset=utf-8"}, error.message)
        logger.error("Error 04 en %s (%s).", nombre, error.code)
        raise web.internalerror("No se pudo completar la operación.") from None


def enviar(usuario: int, mascota: int, respuestas: dict[str, Any]) -> None:
    ejecutar("maow_enviar", {"actor": usuario, "mascota": mascota, "respuestas": respuestas})


def cambiar(usuario: int, solicitud: int, estado: str, motivo: str = "") -> None:
    ejecutar("maow_cambiar", {"actor": usuario, "solicitud": solicitud, "nuevo": estado, "motivo": motivo})
