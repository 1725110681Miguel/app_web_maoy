import web
import logging

from mvc.compartido.sesion import consultar_sesion
from mvc.modulo1_autenticacion.controllers.comun import csrf

logger = logging.getLogger(__name__)

# Renderizador de vistas del Módulo 2 (Catálogo)
render = web.template.render("mvc/modulo2_catalogo/views/")

class Index:
    def GET(self):
        logger.info("Acceso a la página principal (Catálogo de mascotas)")
        usuario = consultar_sesion()
        nombre = web.ctx.session.get("nombre") if usuario else None
        web.header("Cache-Control", "no-store")
        return render.index(usuario, nombre, csrf() if usuario else "")
