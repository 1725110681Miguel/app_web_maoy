# Módulo 5 — Administración y Moderación del Sistema (Yair)

Documentación técnica exclusiva del **Módulo 5** de **AdoPetMyao**, que implementa el requerimiento funcional `RF20`.

---

## 1. Requerimiento cubierto

| Requerimiento | Controlador | Rol autorizado | Descripción |
| :--- | :--- | :--- | :--- |
| **RF20** | `controllers/moderar_cuentas.py` (`ModerarCuentas`) | `Admin` | Lista cuentas filtradas por estado (`Pendiente`, `Activo`, `Suspendido`), permite aprobar o rechazar solicitudes de refugios pendientes, suspender cuentas infractoras (revocando sesiones activas) y reactivar cuentas suspendidas. |

---

## 2. Rutas del módulo

- `GET /modulo5/estilos.css` → Hoja de estilos oficial (`#F8F9FA`, `#154C79`, `#268B86`, `#F4A261`).
- `GET /moderar_cuentas` → Listado general con filtro `?estado=Todos|Pendiente|Activo|Suspendido`.
- `GET|POST /moderar_cuentas/<id_usuario:HASH>` → Expediente de cuenta y formulario de dictamen (`Aprobar`, `Rechazar`, `Suspender`, `Reactivar`).

---

## 3. Base de datos y RPC (`sql/modulo5.sql`)

Ejecuta `sql/modulo5.sql` en el SQL Editor de Supabase para habilitar:
- Columna `motivo_suspension` en `public.usuarios` y políticas RLS para `service_role`.
- `public.maow_moderar_cuenta(admin_id, objetivo_id, accion, motivo)`:
  - Impide que un administrador modere o suspenda su propia cuenta o la de otro administrador.
  - Exige motivo obligatorio en `Rechazar` y `Suspender`.
  - Elimina automáticamente todas las filas de `public.sesiones_abiertas` de la cuenta suspendida/rechazada.
  - Inserta una notificación para el usuario afectado en `public.notificaciones`.

---

## 4. Seguridad implementada (RNT01–RNT03)

- **RNT01 (RBAC):** Solo accesible con sesión válida cuyo rol sea `'Admin'` y estado `'Activo'`.
- **RNT02 (Anti-IDOR):** Todos los enlaces a cuentas utilizan `firmar(id_usuario)` y `validar_enlace(enlace)` (HMAC-SHA256) antes de consultar la base de datos.
- **RNT03 (Anti-CSRF):** Todas las operaciones `POST` validan el token CSRF en sesión mediante `hmac.compare_digest`.

---

## 5. Ejecución de vista previa y pruebas

```bash
# Vista previa visual sin Supabase (puerto 8092)
.venv/bin/python -m mvc.modulo5_administracion.vista_previa

# Pruebas unitarias del Módulo 5
.venv/bin/python -m unittest mvc/modulo5_administracion/test_modulo5.py -v
```
