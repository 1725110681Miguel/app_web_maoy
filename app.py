import web
import logging

# Controlador de la página principal (Catálogo de Mascotas - Módulo 2)
from mvc.modulo2_catalogo.controllers.index import Index

# Configuración del registro de eventos (logging)
logging.basicConfig(
    filename="aplicacion.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",  # Evita errores con tildes o caracteres especiales
)

web.config.debug = False

# Mapeo de rutas (URLs)
urls = (
    '/', 'Index',
    # A medida que vayas creando los controladores de cada módulo, podrás agregarlos aquí:
    # Módulo 1 (Autenticación):
    # '/login', 'mvc.modulo1_autenticacion.controllers.login.Login',
    # '/registro', 'mvc.modulo1_autenticacion.controllers.registro.Registro',
    # '/cerrar_sesion', 'mvc.modulo1_autenticacion.controllers.cerrar_sesion.CerrarSesion',

    # Módulo 2 (Catálogo):
    # '/ver_mascota/(.*)', 'mvc.modulo2_catalogo.controllers.ver_mascota.VerMascota',
    # '/publicar_mascota', 'mvc.modulo2_catalogo.controllers.publicar_mascota.PublicarMascota',
    # '/actualizar_mascota/(.*)', 'mvc.modulo2_catalogo.controllers.actualizar_mascota.ActualizarMascota',
)

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()
