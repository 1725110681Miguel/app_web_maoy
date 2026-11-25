import logging
import os
from pathlib import Path

import web
from dotenv import load_dotenv

from mvc.modulo2_catalogo.controllers.index import Index
from mvc.modulo3_solicitudes.controllers.cancelar_solicitud import CancelarSolicitud
from mvc.modulo3_solicitudes.controllers.cuestionario_aptitud import CuestionarioAptitud
from mvc.modulo3_solicitudes.controllers.enviar_solicitud import EnviarSolicitud
from mvc.modulo3_solicitudes.controllers.evaluar_solicitud import EvaluarSolicitud
from mvc.modulo3_solicitudes.controllers.estilos import Estilos
from mvc.modulo3_solicitudes.controllers.lista_solicitudes import ListaSolicitudes
from mvc.modulo3_solicitudes.controllers.mensajeria_solicitud import MensajeriaSolicitud
from mvc.modulo3_solicitudes.controllers.programar_cita import ProgramarCita

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env")
logging.basicConfig(filename=RAIZ / "aplicacion.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S", encoding="utf-8")
logging.getLogger("httpx").setLevel(logging.WARNING)
web.config.debug = False
web.config.session_parameters.samesite = "Lax"
web.config.session_parameters.secure = os.getenv("COOKIE_SEGURA", "false").lower() == "true"

urls = (
    "/", "Index",
    r"/modulo3/estilos\.css", "Estilos",
    "/cuestionario_aptitud/(.*)", "CuestionarioAptitud",
    "/enviar_solicitud/(.*)", "EnviarSolicitud",
    "/lista_solicitudes", "ListaSolicitudes",
    "/cancelar_solicitud/(.*)", "CancelarSolicitud",
    "/evaluar_solicitud/(.*)", "EvaluarSolicitud",
    "/programar_cita/(.*)", "ProgramarCita",
    "/mensajeria_solicitud/(.*)", "MensajeriaSolicitud",
)

app = web.application(urls, globals())
session = web.session.Session(app, web.session.DiskStore(str(RAIZ / "sessions")), initializer={"token": None})


def preparar_peticion() -> None:
    web.ctx.session = session


app.add_processor(web.loadhook(preparar_peticion))

if __name__ == "__main__":
    app.run()
