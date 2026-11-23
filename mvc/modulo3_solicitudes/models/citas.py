import logging
from mvc.modulo3_solicitudes.models.solicitudes import ejecutar

logger = logging.getLogger(__name__)


def programar(actor: int, solicitud: int, fecha: str, hora: str, lugar: str) -> None:
    ejecutar("maow_cita", {"actor": actor, "solicitud": solicitud, "fecha": fecha, "hora": hora, "sitio": lugar})
