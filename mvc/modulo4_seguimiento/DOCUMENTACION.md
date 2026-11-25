# Módulo 4 — Seguimiento Post-Adopción y Bienestar Animal (Yair)

Documentación técnica exclusiva del **Módulo 4** de **AdoPetMyao**, que implementa los requerimientos funcionales `RF17`, `RF18` y `RF19`.

---

## 1. Requerimientos cubiertos

| Requerimiento | Controlador | Roles autorizados | Descripción |
| :--- | :--- | :--- | :--- |
| **RF17** | `controllers/subir_seguimiento.py` (`SubirSeguimiento`) | `Adoptante` | Lista adopciones cerradas del usuario y permite subir evidencia fotográfica mensual (`.jpg`, `.jpeg`, `.png`, `.webp`) y descripción de bienestar. |
| **RF18** | `controllers/auditar_seguimiento.py` (`AuditarSeguimiento`) | `Publicador`, `Admin` | Consulta reportes e historial por mascota, permite al publicador dueño activar `alerta_maltrato = true`, y al administrador dictaminar (`Sin Novedad`, `En Inspección`, `Rescatado`, `Falsa Alarma`), anotar auditoría y suspender la cuenta del adoptante si procede. |
| **RF19** | `controllers/notificar_seguimiento.py` (`NotificarSeguimiento`) | `Admin` / Cron | Identifica adopciones con más de 30 días naturales sin nuevo reporte fotográfico y genera avisos en `notificaciones`. |

---

## 2. Rutas del módulo

- `GET /modulo4/estilos.css` → Hoja de estilos oficial (`#F8F9FA`, `#154C79`, `#268B86`, `#F4A261`).
- `GET /subir_seguimiento` → Listado de adopciones activas del adoptante.
- `GET|POST /subir_seguimiento/<id_mascota:HASH>` → Formulario y envío de evidencia mensual.
- `GET /auditar_seguimiento` → Panel de auditoría (admite `?filtro=alertas`).
- `GET /auditar_seguimiento/mascota/<id_mascota:HASH>` → Historial de reportes de una mascota.
- `GET|POST /auditar_seguimiento/<id_seguimiento:HASH>` → Expediente detallado, alerta de maltrato y dictamen.
- `GET|POST /notificar_seguimiento` → Panel administrativo de inactividad >30 días y ejecución manual.

---

## 3. Base de datos y RPCs (`sql/modulo4.sql`)

Ejecuta `sql/modulo4.sql` en el SQL Editor de Supabase para habilitar:
- Tabla `public.seguimientos` (con columna `notas_auditoria` y restricción `dictamen_admin`).
- RLS habilitado con acceso exclusivo para `service_role`.
- `public.maow_reporte_seguimiento(actor, mascota, foto, detalle)`
- `public.maow_alerta_maltrato(actor, seguimiento, activar, dictamen, notas, suspender_adoptante)`
- `public.maow_notificar_inactivos_30d(actor)`

---

## 4. Seguridad implementada (RNT01–RNT04)

- **RNT01 (RBAC y Sesión):** Todos los endpoints privados validan sesión cruzada mediante `validar_sesion([...])`. Un `Publicador` solo visualiza y alerta seguimientos de sus propias mascotas.
- **RNT02 (Anti-IDOR):** Todos los enlaces usan `firmar(id)` y `validar_enlace(valor)` (HMAC-SHA256) antes de consultar Supabase.
- **RNT03 (Anti-CSRF):** Todos los formularios `POST` validan el token CSRF de sesión con `hmac.compare_digest` (incluyendo formularios `multipart/form-data`).
- **RNT04 (Archivos):** Validación de extensión (`.jpg`, `.jpeg`, `.png`, `.webp`), tamaño máximo (5 MB), firma binaria (*magic bytes*), prefijo de marca de tiempo en `static/fotos/seguimientos/` y limpieza automática si falla el RPC.

---

## 5. Ejecución de vista previa, rutina RF19 y pruebas

```bash
# Vista previa visual sin Supabase (puerto 8091)
.venv/bin/python -m mvc.modulo4_seguimiento.vista_previa

# Ejecución CLI de la tarea diaria RF19 (>30 días sin reporte)
.venv/bin/python -m mvc.modulo4_seguimiento.controllers.notificar_seguimiento

# Pruebas unitarias del Módulo 4
.venv/bin/python -m unittest mvc/modulo4_seguimiento/test_modulo4.py -v
```
