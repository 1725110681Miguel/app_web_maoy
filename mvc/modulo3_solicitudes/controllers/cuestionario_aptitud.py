import logging

import web

from mvc.compartido.sesion import validar_sesion
from .comun import csrf, denegar, error_formulario, formulario, render, validar_enlace
from ..models.solicitudes import mascota_disponible

logger = logging.getLogger(__name__)


class CuestionarioAptitud:
    def GET(self, enlace: str) -> str:
        mascota = validar_enlace(enlace)
        validar_sesion(["Adoptante"])
        ficha = mascota_disponible(mascota)
        if not ficha:
            denegar()
        return render.cuestionario_aptitud(ficha["nombre"], csrf())

    def POST(self, enlace: str) -> None:
        mascota = validar_enlace(enlace)
        usuario = validar_sesion(["Adoptante"])
        datos = formulario()
        web.ctx.session.borrador = None
        vivienda = datos.get("tipo_vivienda")
        patio = datos.get("tiene_patio")
        motivo = datos.get("motivo_adopcion", "").strip()
        if vivienda not in ("Casa propia", "Departamento", "Renta") or patio not in ("si", "no"):
            error_formulario("Indica el tipo de vivienda y si cuentas con patio seguro.")
        if datos.get("familia_de_acuerdo") != "si" or datos.get("compromiso_gastos") != "si":
            error_formulario("Para continuar necesitas acuerdo familiar y compromiso de cubrir los gastos.")
        if len(motivo) > 1500:
            error_formulario("El motivo admite hasta 1500 caracteres.")
        web.ctx.session.borrador = {
            "usuario": usuario["id_usuario"], "mascota": mascota,
            "respuestas": {"tipo_vivienda": vivienda, "tiene_patio": patio == "si",
                          "familia_de_acuerdo": True, "compromiso_gastos": True, "motivo_adopcion": motivo},
        }
        raise web.seeother("/enviar_solicitud/" + enlace)
