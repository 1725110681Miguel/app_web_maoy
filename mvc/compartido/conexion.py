import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)


def obtener_cliente() -> Client:
    try:
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        url = os.environ["SUPABASE_URL"].strip()
        clave = os.environ["SUPABASE_KEY"].strip()
        if not url or not clave:
            raise ValueError("La configuración de Supabase está incompleta.")
        return create_client(url, clave)
    except Exception as error:
        logger.error("Error 01 al preparar el cliente de Supabase (%s).", type(error).__name__)
        raise RuntimeError("Revisa SUPABASE_URL y SUPABASE_KEY.") from None