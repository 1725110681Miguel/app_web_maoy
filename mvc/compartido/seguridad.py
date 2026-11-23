import hashlib
import hmac
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def firmar(identificador: int) -> str:
    if not 0 < identificador <= 9223372036854775807:
        raise ValueError("Identificador fuera de rango.")
    clave = os.getenv("SECRET_KEY")
    if not clave or not clave.strip():
        logger.error("Error 02. Falta SECRET_KEY.")
        raise RuntimeError("Configura SECRET_KEY.")
    valor = str(identificador)
    firma = hmac.new(clave.encode(), valor.encode(), hashlib.sha256).hexdigest()
    return f"{valor}:{firma}"


def verificar(valor: str) -> int | None:
    if not re.fullmatch(r"[1-9][0-9]{0,18}:[0-9a-f]{64}", valor):
        return None
    identificador = int(valor.split(":")[0])
    if identificador > 9223372036854775807:
        return None
    if hmac.compare_digest(firmar(identificador), valor):
        return identificador
    return None
