from __future__ import annotations

import hmac
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any

try:
    from typing import Never
except ImportError:  # Python < 3.11
    from typing_extensions import Never

import web

from mvc.compartido.seguridad import verificar

logger = logging.getLogger(__name__)
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
CARPETA_FOTOS_SEGUIMIENTO = RAIZ_PROYECTO / "static" / "fotos" / "seguimientos"
EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024

render = web.template.render(str(Path(__file__).resolve().parents[1] / "views"), base="base")


def validar_enlace(valor: str) -> int:
    """Valida una firma HMAC-SHA256 antes de tocar la base de datos."""
    identificador = verificar(valor)
    if identificador is None:
        denegar()
    return identificador


def denegar() -> Never:
    """Aborta la petición con HTTP 404 sin filtrar detalles internos."""
    raise web.notfound("Recurso no encontrado o acceso denegado")


def error_formulario(mensaje: str) -> Never:
    """Responde con HTTP 400 describiendo el error de validación al usuario."""
    raise web.HTTPError("400 Bad Request", {"Content-Type": "text/plain; charset=utf-8"}, mensaje)


def csrf() -> str:
    """Obtiene o genera el token anti-CSRF almacenado en sesión."""
    sesion = web.ctx.session
    if not sesion.get("csrf"):
        sesion.csrf = secrets.token_hex(32)
    return str(sesion.csrf)


def formulario(campos_archivo: dict[str, Any] | None = None) -> Any:
    """Valida el token CSRF en peticiones POST (soporta formularios multipart)."""
    datos = web.input(**campos_archivo) if campos_archivo else web.input()
    recibido = str(datos.get("csrf", ""))
    esperado = str(web.ctx.session.get("csrf", ""))
    if not esperado or not hmac.compare_digest(esperado.encode(), recibido.encode()):
        raise web.forbidden("El formulario caducó. Recarga la página.")
    return datos


def es_imagen_valida(contenido: bytes, extension: str) -> bool:
    """Verifica la firma binaria (magic bytes) acorde a la extensión declarada."""
    if extension in (".jpg", ".jpeg"):
        return contenido.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return contenido.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".webp":
        return len(contenido) >= 12 and contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP"
    return False


def guardar_foto_seguimiento(archivo: Any) -> str:
    """Valida extensión, tamaño y cabecera de imagen; guarda con timestamp en disco."""
    nombre_original = getattr(archivo, "filename", None)
    if not nombre_original:
        error_formulario("Debes seleccionar una fotografía de evidencia.")

    nombre_base = Path(str(nombre_original)).name
    extension = Path(nombre_base).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        error_formulario("Formato no permitido. Usa únicamente imágenes .jpg, .jpeg, .png o .webp.")

    contenido = getattr(archivo, "value", b"")
    if not isinstance(contenido, (bytes, bytearray)) or not contenido:
        error_formulario("El archivo de fotografía está vacío o no pudo leerse.")

    datos_bytes = bytes(contenido)
    if len(datos_bytes) > TAMANO_MAXIMO_BYTES:
        error_formulario("La fotografía supera el límite máximo permitido de 5 MB.")

    if not es_imagen_valida(datos_bytes, extension):
        error_formulario("El contenido del archivo no corresponde a una imagen válida.")

    tallo_limpio = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(nombre_base).stem)[:45] or "evidencia"
    nombre_final = f"{int(time.time())}_{secrets.token_hex(4)}_{tallo_limpio}{extension}"

    try:
        CARPETA_FOTOS_SEGUIMIENTO.mkdir(parents=True, exist_ok=True)
        destino = CARPETA_FOTOS_SEGUIMIENTO / nombre_final
        destino.write_bytes(datos_bytes)
    except OSError as error:
        logger.error("Error 09 al guardar fotografía de seguimiento (%s).", type(error).__name__)
        raise web.internalerror("No se pudo almacenar la fotografía en el servidor.") from None

    return nombre_final


def eliminar_foto_seguimiento(nombre_archivo: str) -> None:
    """Elimina físicamente una fotografía previa del disco si existe y es válida."""
    if not nombre_archivo or nombre_archivo == "mascota_default.webp":
        return
    nombre_seguro = Path(nombre_archivo).name
    if nombre_seguro != nombre_archivo:
        return
    ruta = str(CARPETA_FOTOS_SEGUIMIENTO / nombre_seguro)
    try:
        if os.path.exists(ruta):
            os.remove(ruta)
    except OSError as error:
        logger.warning("Error 10 al limpiar fotografía de seguimiento (%s).", type(error).__name__)
