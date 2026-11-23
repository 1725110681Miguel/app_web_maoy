import web
import logging

logger = logging.getLogger(__name__)

# Renderizador de vistas del Módulo 2 (Catálogo)
render = web.template.render("mvc/modulo2_catalogo/views/")

class Index:
    def GET(self):
        logger.info("Acceso a la página principal (Catálogo de mascotas)")
        return render.index()
