import logging
from typing import Any

from mvc.modulo3_solicitudes.models.solicitudes import ejecutar

logger = logging.getLogger(__name__)


def historial(actor: int, solicitud: int) -> list[dict[str, Any]]:
    return ejecutar("maow_chat", {"actor": actor, "solicitud": solicitud, "texto": None})


def enviar(actor: int, solicitud: int, contenido: str) -> None:
    ejecutar("maow_chat", {"actor": actor, "solicitud": solicitud, "texto": contenido})
