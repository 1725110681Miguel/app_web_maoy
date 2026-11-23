import logging
from typing import Any

from mvc.compartido.conexion import obtener_cliente

logger = logging.getLogger(__name__)


def recientes(usuario: int) -> list[dict[str, Any]]:
    return (obtener_cliente().table("notificaciones").select("mensaje,fecha_creacion")
            .eq("id_usuario", usuario).order("id_notificacion", desc=True).limit(10).execute().data)
