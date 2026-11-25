from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, TypedDict

import web
from postgrest.exceptions import APIError

from mvc.compartido.conexion import obtener_cliente
from mvc.compartido.sesion import Usuario

logger = logging.getLogger(__name__)

CAMPOS_SEGUIMIENTO = (
    "id_seguimiento,id_mascota,id_adoptante,foto_evidencia,comentario,"
    "fecha_reporte,alerta_maltrato,dictamen_admin,notas_auditoria,"
    "mascotas!inner(id_mascota,nombre,especie,raza,id_publicador,estado_adopcion),"
    "usuarios!inner(id_usuario,nombre_completo,correo,estado_cuenta)"
)


class ResumenAdopcion(TypedDict):
    id_mascota: int
    nombre: str
    especie: str
    raza: str
    foto: str
    fecha_adopcion: str
    ultimo_reporte: str | None
    dias_sin_reporte: int
    atrasado: bool


class CasoAtrasado(TypedDict):
    id_mascota: int
    nombre_mascota: str
    especie: str
    adoptante: str
    correo_adoptante: str
    ultima_actividad: str
    dias_sin_reporte: int


def ejecutar(nombre: str, parametros: dict[str, Any]) -> Any:
    """Ejecuta una función almacenada RPC de Supabase traduciendo errores de negocio."""
    try:
        return obtener_cliente().rpc(nombre, parametros).execute().data
    except APIError as error:
        if error.code == "P0001":
            raise web.HTTPError("409 Conflict", {"Content-Type": "text/plain; charset=utf-8"}, error.message)
        logger.error("Error 08 en RPC %s (%s).", nombre, error.code)
        raise web.internalerror("No se pudo completar la operación en base de datos.") from None


def _parsear_fecha(valor: str | None) -> datetime:
    if not valor:
        return datetime.now(timezone.utc)
    texto = valor.replace("Z", "+00:00")
    fecha = datetime.fromisoformat(texto)
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha


def adopciones_adoptante(id_adoptante: int) -> list[ResumenAdopcion]:
    """Obtiene las mascotas adoptadas por el usuario y el estado de su último reporte."""
    cliente = obtener_cliente()
    solicitudes = (
        cliente.table("solicitudes")
        .select("id_mascota,fecha_solicitud,mascotas!inner(id_mascota,nombre,especie,raza,foto,estado_adopcion)")
        .eq("id_adoptante", id_adoptante)
        .eq("estado_solicitud", "Aprobada")
        .eq("mascotas.estado_adopcion", "Adoptada")
        .order("fecha_solicitud", desc=True)
        .execute()
        .data
    )
    if not solicitudes:
        return []

    ids_mascotas = [int(fila["id_mascota"]) for fila in solicitudes]
    reportes = (
        cliente.table("seguimientos")
        .select("id_mascota,fecha_reporte")
        .eq("id_adoptante", id_adoptante)
        .in_("id_mascota", ids_mascotas)
        .order("fecha_reporte", desc=True)
        .execute()
        .data
    )
    ultimo_por_mascota: dict[int, str] = {}
    for rep in reportes:
        mid = int(rep["id_mascota"])
        if mid not in ultimo_por_mascota:
            ultimo_por_mascota[mid] = rep["fecha_reporte"]

    ahora = datetime.now(timezone.utc)
    resultado: list[ResumenAdopcion] = []
    vistos: set[int] = set()
    for sol in solicitudes:
        mid = int(sol["id_mascota"])
        if mid in vistos:
            continue
        vistos.add(mid)
        mascota = sol["mascotas"]
        ultimo = ultimo_por_mascota.get(mid)
        referencia = _parsear_fecha(ultimo or sol["fecha_solicitud"])
        dias = max(0, (ahora - referencia).days)
        resultado.append(
            ResumenAdopcion(
                id_mascota=mid,
                nombre=mascota["nombre"],
                especie=mascota["especie"],
                raza=mascota["raza"],
                foto=mascota["foto"],
                fecha_adopcion=str(sol["fecha_solicitud"])[:10],
                ultimo_reporte=str(ultimo)[:10] if ultimo else None,
                dias_sin_reporte=dias,
                atrasado=dias > 30,
            )
        )
    return resultado


def verificar_adopcion_adoptante(id_adoptante: int, id_mascota: int) -> dict[str, Any] | None:
    """Verifica que el adoptante tenga una adopción aprobada y cerrada para la mascota."""
    filas = (
        obtener_cliente()
        .table("solicitudes")
        .select("id_solicitud,mascotas!inner(id_mascota,nombre,especie,estado_adopcion)")
        .eq("id_adoptante", id_adoptante)
        .eq("id_mascota", id_mascota)
        .eq("estado_solicitud", "Aprobada")
        .eq("mascotas.estado_adopcion", "Adoptada")
        .limit(1)
        .execute()
        .data
    )
    return filas[0] if filas else None


def registrar_reporte(actor: int, mascota: int, foto: str, comentario: str) -> int:
    """Registra un reporte mensual de seguimiento mediante RPC transaccional."""
    resultado = ejecutar(
        "maow_reporte_seguimiento",
        {"actor": actor, "mascota": mascota, "foto": foto, "detalle": comentario},
    )
    return int(resultado) if resultado is not None else 0


def listar_auditoria(
    usuario: Usuario,
    id_mascota: int | None = None,
    id_seguimiento: int | None = None,
    solo_alertas: bool = False,
) -> list[dict[str, Any]]:
    """Lista los reportes de seguimiento visibles para el publicador dueño o el administrador."""
    cliente = obtener_cliente()
    filas: list[dict[str, Any]] = []
    while True:
        consulta = cliente.table("seguimientos").select(CAMPOS_SEGUIMIENTO)
        if usuario["rol"] == "Publicador":
            consulta = consulta.eq("mascotas.id_publicador", usuario["id_usuario"])
        if id_mascota is not None:
            consulta = consulta.eq("id_mascota", id_mascota)
        if id_seguimiento is not None:
            consulta = consulta.eq("id_seguimiento", id_seguimiento)
        if solo_alertas:
            consulta = consulta.eq("alerta_maltrato", True)
        consulta = (
            consulta.order("alerta_maltrato", desc=True)
            .order("fecha_reporte", desc=True)
            .order("id_seguimiento", desc=True)
        )
        pagina = consulta.range(len(filas), len(filas) + 199).execute().data
        filas.extend(pagina)
        if not pagina or id_seguimiento is not None:
            return filas


def detalle_auditoria(usuario: Usuario, id_seguimiento: int) -> dict[str, Any]:
    """Obtiene un reporte específico verificando propiedad si el actor es Publicador."""
    filas = listar_auditoria(usuario, id_seguimiento=id_seguimiento)
    if not filas:
        raise web.notfound("Recurso no encontrado o acceso denegado")
    return filas[0]


def aplicar_auditoria(
    actor: int,
    seguimiento: int,
    activar: bool,
    dictamen: str | None = None,
    notas: str | None = None,
    suspender_adoptante: bool = False,
) -> None:
    """Ejecuta alerta de maltrato o dictamen de auditoría vía RPC."""
    ejecutar(
        "maow_alerta_maltrato",
        {
            "actor": actor,
            "seguimiento": seguimiento,
            "activar": activar,
            "dictamen": dictamen,
            "notas": notas,
            "suspender_adoptante": suspender_adoptante,
        },
    )


def adopciones_atrasadas(dias_limite: int = 30) -> list[CasoAtrasado]:
    """Identifica adopciones que superaron el plazo sin nuevo reporte fotográfico."""
    cliente = obtener_cliente()
    solicitudes = (
        cliente.table("solicitudes")
        .select(
            "id_mascota,fecha_solicitud,"
            "mascotas!inner(id_mascota,nombre,especie,estado_adopcion),"
            "usuarios!inner(nombre_completo,correo)"
        )
        .eq("estado_solicitud", "Aprobada")
        .eq("mascotas.estado_adopcion", "Adoptada")
        .order("fecha_solicitud", desc=True)
        .execute()
        .data
    )
    if not solicitudes:
        return []

    ids_mascotas = list({int(fila["id_mascota"]) for fila in solicitudes})
    reportes = (
        cliente.table("seguimientos")
        .select("id_mascota,fecha_reporte")
        .in_("id_mascota", ids_mascotas)
        .order("fecha_reporte", desc=True)
        .execute()
        .data
    )
    ultimo_por_mascota: dict[int, str] = {}
    for rep in reportes:
        mid = int(rep["id_mascota"])
        if mid not in ultimo_por_mascota:
            ultimo_por_mascota[mid] = rep["fecha_reporte"]

    ahora = datetime.now(timezone.utc)
    atrasados: list[CasoAtrasado] = []
    vistos: set[int] = set()
    for sol in solicitudes:
        mid = int(sol["id_mascota"])
        if mid in vistos:
            continue
        vistos.add(mid)
        ultima = ultimo_por_mascota.get(mid) or sol["fecha_solicitud"]
        dias = max(0, (ahora - _parsear_fecha(ultima)).days)
        if dias > dias_limite:
            atrasados.append(
                CasoAtrasado(
                    id_mascota=mid,
                    nombre_mascota=sol["mascotas"]["nombre"],
                    especie=sol["mascotas"]["especie"],
                    adoptante=sol["usuarios"]["nombre_completo"],
                    correo_adoptante=sol["usuarios"]["correo"],
                    ultima_actividad=str(ultima)[:10],
                    dias_sin_reporte=dias,
                )
            )
    atrasados.sort(key=lambda item: item["dias_sin_reporte"], reverse=True)
    return atrasados


def notificar_inactivos(actor: int | None = None) -> int:
    """Dispara la rutina SQL que genera advertencias para adopciones inactivas >30 días."""
    resultado = ejecutar("maow_notificar_inactivos_30d", {"actor": actor})
    return int(resultado) if resultado is not None else 0
