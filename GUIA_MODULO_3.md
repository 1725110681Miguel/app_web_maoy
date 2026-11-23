# AdopetMAOW · Solicitudes de adopción

## Incorporación al repositorio

El ZIP contiene los archivos de esta entrega con sus rutas relativas a la raíz de app_web_maoy. Descomprímelo desde esa carpeta. Incluye la versión integrada de app.py y agrega el enlace «Mis solicitudes» a la navegación de la portada existente. Si alguien editó esos archivos después del 23 de noviembre, integra sus cambios antes de sustituirlos.

## Configuración local

1. Desde la raíz del repositorio, crea y activa el entorno de Python 3.12.
2. Instala las dependencias, copia .env.example a .env si todavía no tienes uno y completa sus valores.
3. En el editor SQL de Supabase, ejecuta sql/modulo3.sql después de que el equipo cree usuarios, mascotas, solicitudes y sesiones_abiertas con las relaciones y columnas del spec.
4. Arranca la aplicación desde la raíz del repositorio.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia la cadena generada a SECRET_KEY. Los módulos de una misma instalación deben usar la misma clave para reconocer los enlaces firmados. SUPABASE_URL es la dirección del proyecto. SUPABASE_KEY debe contener una clave secreta de servidor con permisos de service_role. Guárdala exclusivamente en el servidor. Para desarrollo con HTTP local, usa COOKIE_SEGURA=false. En el despliegue con HTTPS, configura COOKIE_SEGURA=true.

```sh
python app.py
```

## Integración con el equipo

- Autenticación. El equipo del módulo 1 debe registrar /login y, después de autenticar correctamente al usuario, guardar el JWT de acceso en web.ctx.session.token e insertarlo en sesiones_abiertas con el id_usuario correspondiente. El correo de usuarios debe coincidir con el de Supabase Auth. La cuenta debe estar Activa (valor de estado_cuenta: Activo). El cierre de sesión debe revocar el registro y destruir la sesión local. app.py ya inicializa una sola sesión para todos los módulos.
- Catálogo. El botón «Solicitar adopción» de cada ficha debe apuntar a la ruta formada por "/cuestionario_aptitud/" + firmar(id_mascota). El enlace «Mis solicitudes» de la portada ya abre la lista personal. El catálogo actual es una maqueta y aún carece de fichas individuales.
- Administración. El equipo del módulo 5 realiza el cambio a En Proceso. El publicador evalúa el estado de la solicitud en RF14 y el equipo del módulo 2 cierra la adopción en RF08.
- Base de datos. Las escrituras y sus avisos se guardan juntos mediante funciones PostgreSQL. Esas funciones solo se conceden al rol de servidor. La migración también restringe el acceso directo de anon y authenticated a solicitudes, sesiones_abiertas, notificaciones, citas y mensajes. El equipo deberá acceder a estas tablas mediante los controladores del servidor. Las políticas de usuarios y mascotas corresponden a los módulos que administran esas tablas.

## Qué hace cada archivo

Las rutas siguientes parten de la raíz del proyecto.

| Archivo en mvc/compartido | Función |
| --- | --- |
| conexion.py | Lee la configuración y crea el cliente oficial de Supabase para el servidor. |
| seguridad.py | Firma un identificador y comprueba que la firma que vuelve en la URL corresponda al mismo número. |
| sesion.py | Verifica el JWT con Supabase Auth y comprueba su registro, propietario, estado de cuenta y rol. |

Cada fila siguiente corresponde a un archivo Python de mvc/modulo3_solicitudes/controllers y a la plantilla del mismo nombre en views, con extensión .html.

| Controlador y vista | Qué hace el controlador | Qué muestra la vista |
| --- | --- | --- |
| cuestionario_aptitud | Valida las respuestas y guarda un borrador vinculado a usuario y mascota en la sesión. Exige acuerdo familiar y compromiso de gastos. | Las cuatro preguntas y un motivo opcional. |
| enviar_solicitud | Requiere el borrador correcto. Al confirmar, vuelve a comprobar disponibilidad y duplicados en la base, guarda la solicitud pendiente y avisa al publicador. | Las respuestas y el botón de confirmación. |
| lista_solicitudes | Selecciona las enviadas o recibidas por la cuenta actual y firma los enlaces. | Mascota, fecha, estado, acciones, motivo de rechazo y avisos recientes. |
| cancelar_solicitud | Permite al adoptante cancelar su solicitud activa. Avisa al publicador y libera la mascota si estaba en proceso y ya no quedan solicitudes activas. | Confirmación de cancelación. |
| evaluar_solicitud | Permite al dueño de la publicación evaluar una solicitud pendiente. Exige motivo al rechazar y avisa al adoptante. | Respuestas, decisión y motivo. |
| programar_cita | Guarda una cita futura para una solicitud aprobada del publicador y avisa al adoptante con los detalles. | Fecha, hora local del centro de México y lugar. |
| mensajeria_solicitud | Verifica participación y solicitud activa, guarda mensajes y marca como leídos los recibidos al consultar el historial. | Historial cronológico, estado de lectura y formulario de envío. |

| Otro archivo | Función |
| --- | --- |
| mvc/modulo3_solicitudes/controllers/comun.py | Reúne la validación de enlaces, los errores, la protección de los formularios y el renderizado. |
| mvc/modulo3_solicitudes/models/solicitudes.py | Consulta mascotas y solicitudes con filtros de pertenencia. Invoca las operaciones de envío y cambio de estado. |
| mvc/modulo3_solicitudes/models/notificaciones.py | Obtiene los diez avisos más recientes del usuario. Cada operación genera su aviso en la misma transacción SQL. |
| mvc/modulo3_solicitudes/models/citas.py | Envía la fecha, hora y lugar a la operación de citas. |
| mvc/modulo3_solicitudes/models/mensajes.py | Invoca las operaciones de envío y lectura del chat. |
| mvc/modulo3_solicitudes/views/base.html | Define la navegación y estructura común de las siete pantallas. |
| static/css/solicitudes.css | Aplica la paleta del proyecto y adapta formularios y tablas a celular y computadora. |
| sql/modulo3.sql | Agrega motivo_rechazo, crea las tres tablas acordadas, las funciones de escritura y sus permisos. |
| app.py | Registra las rutas y hace que todos los controladores usen la misma sesión de web.py. |

Una solicitud se considera activa cuando está Pendiente o Aprobada y la mascota sigue sin adoptarse. La vivienda y el patio se muestran al publicador para su valoración. El identificador firmado conserva el formato id:HASH del spec. La firma permite detectar modificaciones y los controles de pertenencia determinan quién puede actuar sobre ese registro.
