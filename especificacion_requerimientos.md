# 3.1 Especificación de Requerimientos: Aplicación Web Segura para la Adopción Responsable de Mascotas v23.11.2026.2

---

## 1. Objetivo
Desarrollar una aplicación web bajo el patrón arquitectónico **Modelo-Vista-Controlador (MVC)** para la gestión responsable y segura de adopciones de perros y gatos. El sistema implementa autenticación de usuarios con roles diferenciados (*Adoptante*, *Publicador/Refugio* y *Administrador*), control de acceso basado en sesiones persistentes validadas contra base de datos y protección criptográfica de parámetros en URLs mediante firmas **HMAC/HASH** para prevenir ataques de referencia directa insegura a objetos (**IDOR**).

---

## 2. Reglas de Negocio y Seguridad Transversales (RNT)

### RNT01 - Protección de rutas privadas y control de acceso basado en roles
1. Todas las vistas y controladores privados de la aplicación (publicación, gestión de solicitudes, mensajería, seguimiento y panel de administración) deben validar obligatoriamente antes de ejecutarse que exista una cookie/variable de sesión activa en `web.py` y que el token de sesión coincida con un registro vigente en la tabla `sesiones_abiertas` de Supabase.
2. Cada controlador debe validar adicionalmente que el usuario posea el **rol autorizado** para la acción solicitada (*Adoptante*, *Publicador* o *Admin*). Cada usuario únicamente podrá consultar y modificar los registros asociados a su cuenta.
3. Si la sesión no existe, expiró o el rol es insuficiente, el sistema debe redirigir inmediatamente a la vista de `login`.

### RNT02 - Generación y validación de URLs firmadas (Anti-IDOR mediante HASH)
1. Ningún identificador numérico de entidades sensibles (`id_mascota`, `id_solicitud`, `id_seguimiento`, `id_usuario`) debe exponerse en claro dentro de las URLs.
2. El sistema generará una firma criptográfica en memoria combinando el identificador y una `SECRET_KEY` utilizando el algoritmo **HMAC-SHA256**, bajo el formato:  
   `"identificador:HASH"` (por ejemplo: `id_mascota:HASH` o `id_solicitud:HASH`).
3. El controlador receptor verificará la firma antes de consultar la base de datos. Si el HASH no coincide o fue alterado, la petición se descartará inmediatamente mostrando un error de "Recurso no encontrado o acceso denegado", sin consultar la base de datos.

---

## 3. Requerimientos Técnicos y Tecnológicos (RTT)

### RTT01 - Stack Tecnológico y Arquitectura
**Backend:**
1. **Lenguaje de programación:** Python 3.12.
2. **Prácticas de implementación:** Tipado estático estricto (`typing`), manejo de excepciones numerado mediante bloques `try/except` y registro de actividad mediante `logging.getLogger(__name__)` en cada módulo.
3. **Framework web:** Microframework `web.py`.
4. **Arquitectura:** Patrón Modelo-Vista-Controlador (MVC) con **controladores de acción única** (`login.py`, `registro.py`, `cerrar_sesion.py`, `catalogo.py`, `ver_mascota.py`, `publicar_mascota.py`, `actualizar_mascota.py`, `cerrar_adopcion.py`, `favoritos_mascota.py`, `cuestionario_aptitud.py`, `enviar_solicitud.py`, `lista_solicitudes.py`, `cancelar_solicitud.py`, `evaluar_solicitud.py`, `programar_cita.py`, `mensajeria_solicitud.py`, `subir_seguimiento.py`, `auditar_seguimiento.py`, `notificar_seguimiento.py`, `moderar_cuentas.py`).

**Frontend:**
1. HTML5 semántico y accesible.
2. CSS3 basado en la paleta oficial: Blanco Humo (`#F8F9FA`), Azul Marino (`#154C79`), Verde Agua (`#268B86`) y Naranja Coral (`#F4A261`).
3. JavaScript vanilla (sin frameworks pesados).
4. Motor de plantillas: `web.template.render` de `web.py`.

---

### RTT02 - Integración con Backend as a Service (Supabase)
**Librería de conexión:**
1. SDK oficial `supabase` para Python (`supabase-py`), configurado mediante variables de entorno (`SUPABASE_URL` y `SUPABASE_KEY`) cargadas desde el archivo `.env` mediante `python-dotenv`.

**Servicios utilizados:**
1. **Supabase Authentication:** Validación de credenciales de acceso (`sign_in_with_password`), registro seguro con hash de contraseñas y gestión de tokens JWT de sesión.
2. **Supabase Database (PostgreSQL):** Persistencia de datos mediante consultas parametrizadas desde la capa de Modelo hacia las tablas del sistema.

---

### RTT03 - Estructura de Datos (Esquema de Base de Datos)
La base de datos en Supabase contiene las siguientes entidades principales:

1. **Tabla `usuarios`:**
   * `id_usuario` (bigint / int8, Primary Key, autoincremental).
   * `nombre_completo` (varchar / text, obligatorio).
   * `correo` (varchar / text, único, obligatorio).
   * `password` (varchar / text, obligatorio, cifrado).
   * `telefono` (varchar / text, obligatorio).
   * `direccion` (varchar / text, obligatorio).
   * `rol` (varchar / text, obligatorio: `'Adoptante'`, `'Publicador'`, `'Admin'`).
   * `estado_cuenta` (varchar / text, `'Activo'`, `'Pendiente'`, `'Suspendido'`).

2. **Tabla `mascotas`:**
   * `id_mascota` (bigint / int8, Primary Key, autoincremental).
   * `id_publicador` (bigint / int8, Foreign Key -> `usuarios.id_usuario`).
   * `nombre` (varchar / text, obligatorio).
   * `especie` (varchar / text, obligatorio: `'Perro'`, `'Gato'`).
   * `raza` (varchar / text, obligatorio).
   * `edad` (int4 / integer, edad aproximada en meses o años).
   * `tamano` (varchar / text: `'Chico'`, `'Mediano'`, `'Grande'`).
   * `personalidad` (varchar / text, descripción del carácter).
   * `salud` (varchar / text, estado general de salud).
   * `vacunas` (varchar / text, esquema de vacunación).
   * `ubicacion` (varchar / text, municipio o ciudad).
   * `foto` (varchar / text, nombre del archivo de imagen).
   * `estado_adopcion` (varchar / text: `'Disponible'`, `'En Proceso'`, `'Adoptada'`).

3. **Tabla `solicitudes`:**
   * `id_solicitud` (bigint / int8, Primary Key, autoincremental).
   * `id_mascota` (bigint / int8, Foreign Key -> `mascotas.id_mascota`).
   * `id_adoptante` (bigint / int8, Foreign Key -> `usuarios.id_usuario`).
   * `tipo_vivienda` (varchar / text, casa propia, departamento, renta).
   * `tiene_patio` (boolean, obligatorio).
   * `familia_de_acuerdo` (boolean, obligatorio).
   * `compromiso_gastos` (boolean, solvencia para alimento y veterinario).
   * `motivo_adopcion` (text, justificación de adopción).
   * `estado_solicitud` (varchar / text: `'Pendiente'`, `'Aprobada'`, `'Rechazada'`, `'Cancelada'`).
   * `fecha_solicitud` (timestamp / date, fecha de registro).

4. **Tabla `seguimientos`:**
   * `id_seguimiento` (bigint / int8, Primary Key, autoincremental).
   * `id_mascota` (bigint / int8, Foreign Key -> `mascotas.id_mascota`).
   * `id_adoptante` (bigint / int8, Foreign Key -> `usuarios.id_usuario`).
   * `foto_evidencia` (varchar / text, nombre del archivo de imagen).
   * `comentario` (text, descripción de cuidados y salud actual).
   * `fecha_reporte` (timestamp / date, fecha de envío).
   * `alerta_maltrato` (boolean, falso por defecto; verdadero ante sospecha de maltrato).
   * `dictamen_admin` (varchar / text, `'Sin Novedad'`, `'En Inspección'`, `'Rescatado'`).

5. **Tabla `sesiones_abiertas`:**
   * `token` (varchar / text, Primary Key, obligatorio): Almacena los tokens JWT de sesión vigentes para validar cada petición contra la cookie de sesión de `web.py`.
   * `id_usuario` (bigint / int8, Foreign Key -> `usuarios.id_usuario`).
   * `fecha_creacion` (timestamp, fecha y hora de inicio de sesión).

---

### RTT04 - Gestión de Archivos Estáticos (Imágenes)
**Almacenamiento local:**
1. Las fotografías de las mascotas en adopción y las fotografías de evidencia de seguimiento se almacenarán en el sistema de archivos local del servidor dentro de `static/fotos/` (organizadas opcionalmente en `static/fotos/mascotas/` y `static/fotos/seguimientos/`).

**Integridad y limpieza de archivos:**
1. Al subir una foto, el controlador validará estrictamente la extensión del archivo (`.jpg`, `.jpeg`, `.png`, `.webp`).
2. Se evitarán colisiones de nombres anteponiendo una marca de tiempo al nombre del archivo (`timestamp_archivo.ext`).
3. Al actualizar la fotografía de una mascota o al eliminar un registro, el servidor eliminará físicamente el archivo anterior en `static/fotos/` (verificando previamente su existencia con `os.path.exists` y omitiendo imágenes por defecto).

---

### RTT05 - Seguridad y Protección de URLs
1. **Firma criptográfica (Anti-IDOR):** El módulo de seguridad utilizará las librerías estándar `hmac` y `hashlib` (algoritmo HMAC-SHA256) empleando una `SECRET_KEY` configurada en `.env` para generar y verificar las cadenas `id:HASH` en todas las operaciones de visualización, edición, aprobación y seguimiento.
2. **Control de sesiones:** Uso del gestor de sesiones de `web.py` (`web.session`) respaldado por la validación cruzada obligatoria contra el campo `token` de la tabla `sesiones_abiertas` en Supabase en cada solicitud a rutas protegidas.

---

## 4. Módulo 1: Autenticación y Gestión de Usuarios

### RF01 - Registro de usuario y solicitud de alta de refugio (registro)
* **Descripción:** Permite a un nuevo usuario crear una cuenta eligiendo rol de Adoptante o solicitar registro como Refugio/Publicador.
* **Flujo principal:**
  1. El usuario completa el formulario con: nombre completo, correo, contraseña, teléfono, dirección y rol deseado.
  2. Si selecciona rol *Adoptante*, la cuenta se crea con estado `'Activo'`. Si selecciona *Publicador/Refugio*, se registra con estado `'Pendiente'` para revisión del administrador.
  3. El controlador inserta el registro en la tabla `usuarios` y redirige a `login` con mensaje de confirmación.
* **Flujo alternativo (Error):**
  1. Si el correo ya está registrado o faltan campos obligatorios, el sistema permanece en el formulario mostrando el mensaje de error correspondiente.

### RF02 - Inicio de sesión (login)
* **Descripción:** Permite a un usuario registrado autenticarse en el sistema.
* **Flujo principal:**
  1. El usuario ingresa su email y contraseña en la vista `login`.
  2. El controlador valida las credenciales contra Supabase Authentication y consulta el rol y estado en la tabla `usuarios`.
  3. Si la cuenta está en estado `'Pendiente'`, el sistema impide el acceso e indica que su registro está en revisión por el administrador. Si está `'Suspendido'`, notifica el bloqueo.
  4. Si las credenciales y el estado son válidos, el sistema guarda el token en una cookie segura de sesión, inserta el token en la tabla `sesiones_abiertas` de Supabase y redirige al catálogo de mascotas (`index`).
* **Flujo alternativo (Error):**
  1. Si las credenciales son incorrectas, muestra: *"Credenciales incorrectas, verifique sus datos"*.

### RF03 - Cerrar sesión (cerrar_sesion)
* **Descripción:** Finaliza de manera segura la sesión del usuario.
* **Flujo principal:**
  1. El usuario presiona el botón "Cerrar sesión".
  2. El controlador elimina el registro del token en la tabla `sesiones_abiertas` de Supabase.
  3. El sistema destruye la sesión local de `web.py` y redirige a `login`.

---

## 5. Módulo 2: Catálogo y Publicaciones de Mascotas

### RF04 - Página principal y búsqueda con filtros (catalogo)
* **Descripción:** Muestra el catálogo de perros y gatos disponibles para adopción con filtros de búsqueda.
* **Flujo principal:**
  1. El controlador consulta las mascotas con estado `'Disponible'` en Supabase.
  2. El usuario puede filtrar por: especie (perro/gato), edad, tamaño y ubicación.
  3. El controlador calcula para cada mascota su identificador firmado `id_mascota:HASH` y renderiza las tarjetas con foto, nombre, edad, especie y enlace firmado a `ver_mascota`.

### RF05 - Ver detalle de mascota (ver_mascota)
* **Descripción:** Presenta la ficha completa de una mascota específica.
* **Flujo principal:**
  1. El controlador recibe el parámetro `id_mascota:HASH` por URL y verifica la integridad del HASH.
  2. Si es válido, consulta los datos en la tabla `mascotas` (salud, vacunas, personalidad, ubicación) y muestra el botón "Solicitar Adopción" (si es adoptante) o "Guardar en Favoritos".
* **Flujo alternativo (Error):**
  1. Si el HASH fue alterado o la mascota no existe, muestra *"Mascota no encontrada"* y redirige al catálogo.

### RF06 - Publicar nueva mascota (publicar_mascota)
* **Descripción:** Permite a un publicador o refugio registrar una mascota para adopción.
* **Flujo principal:**
  1. El publicador autenticado llena el formulario: nombre, especie, raza, edad, tamaño, personalidad, salud, vacunas, ubicación y sube una fotografía.
  2. El controlador valida campos obligatorios y formato de imagen, guarda la foto en `static/fotos/` con timestamp e inserta el registro en la tabla `mascotas` con estado `'Disponible'`.
  3. Redirige a la lista de mascotas del publicador con mensaje de éxito.
* **Flujo alternativo:**
  1. Si faltan datos obligatorios o la imagen no es válida, resalta los campos erróneos sin guardar.

### RF07 - Modificar y actualizar mascota (actualizar_mascota)
* **Descripción:** Permite al publicador dueño de la mascota actualizar sus datos o fotografías.
* **Flujo principal:**
  1. El controlador recibe `id_mascota:HASH`, valida el HASH y comprueba que la mascota pertenezca al publicador en sesión.
  2. Muestra el formulario con los datos actuales. Al guardar, actualiza la información en Supabase (reemplazando físicamente la foto anterior en disco solo si se subió una nueva).
  3. Muestra mensaje de confirmación y redirige a la lista de publicaciones.
* **Flujo alternativo:**
  1. Si el HASH es inválido o el usuario no es el dueño original, rechaza el acceso con mensaje de error.

### RF08 - Marcar como adoptada y cerrar publicación (cerrar_adopcion)
* **Descripción:** Cierra el proceso de adopción de una mascota entregada.
* **Flujo principal:**
  1. El publicador selecciona una mascota con solicitud aprobada y presiona "Confirmar Adopción".
  2. El controlador valida `id_mascota:HASH`, cambia el estado de la mascota a `'Adoptada'`, la oculta del catálogo público y activa el periodo de seguimiento de fotos mensuales.

### RF09 - Guardar y gestionar mascotas favoritas (favoritos_mascota)
* **Descripción:** Permite a un usuario con rol 'Adoptante' guardar y consultar su lista personal de mascotas de interés.
* **Flujo principal:**
  1. Desde `ver_mascota` o `catalogo`, el adoptante presiona "Guardar en Favoritos" o "Quitar de Favoritos" enviando `id_mascota:HASH`.
  2. El controlador valida sesión activa, rol 'Adoptante' y firma HMAC-SHA256 del identificador.
  3. Inserta o elimina el vínculo en la base de datos y muestra el estado actualizado.
  4. En la vista de favoritos del adoptante, consulta las mascotas guardadas generando sus enlaces firmados `id_mascota:HASH`.
* **Flujo alternativo (Error):**
  1. Si el HASH es alterado o la mascota no existe, muestra *"Mascota no encontrada"* y redirige al catálogo.

---

## 6. Módulo 3: Cuestionario, Solicitudes y Comunicación

### RF10 - Cuestionario de aptitud para adopción (cuestionario_aptitud)
* **Descripción:** Evalúa si el interesado cumple con las condiciones mínimas para tener una mascota.
* **Flujo principal:**
  1. El adoptante responde preguntas sobre: tipo de vivienda (casa/departamento), si cuenta con patio seguro, acuerdo de la familia y compromiso para gastos médicos y alimentación.
  2. El controlador valida que las respuestas demuestren aptitud antes de habilitar el envío de la solicitud formal.

### RF11 - Enviar solicitud de adopción (enviar_solicitud)
* **Descripción:** Vincula al adoptante con la mascota deseada mediante una solicitud formal.
* **Flujo principal:**
  1. Con el cuestionario validado, el adoptante confirma el envío de su solicitud para la mascota disponible.
  2. El controlador verifica que la mascota siga disponible y que el usuario no tenga otra solicitud activa para el mismo animal.
  3. Guarda el registro en la tabla `solicitudes` con estado `'Pendiente'` y fecha actual. Notifica al publicador responsable.

### RF12 - Consultar estado de solicitudes (lista_solicitudes)
* **Descripción:** Permite visualizar las solicitudes enviadas (adoptante) o recibidas (publicador).
* **Flujo principal:**
  1. El controlador consulta las solicitudes correspondientes al usuario en sesión.
  2. Genera los enlaces protegidos con `id_solicitud:HASH` para cada acción.
  3. Muestra tabla con: mascota, fecha, estado (`'Pendiente'`, `'Aprobada'`, `'Rechazada'`, `'Cancelada'`) y opciones.

### RF13 - Cancelar o desistir de una solicitud de adopción (cancelar_solicitud)
* **Descripción:** Permite al adoptante retirar una solicitud en estado `'Pendiente'` o `'Aprobada'` antes de cerrar la adopción.
* **Flujo principal:**
  1. El adoptante selecciona "Cancelar solicitud" enviando `id_solicitud:HASH`.
  2. El controlador verifica el HASH, comprueba que la solicitud pertenezca al adoptante en sesión y que su estado actual permita cancelación.
  3. Actualiza `estado_solicitud` a `'Cancelada'` y notifica al publicador responsable.
  4. Si la mascota estaba en `'En Proceso'` sin otras solicitudes, la retorna a `'Disponible'`.
* **Flujo alternativo (Error):**
  1. Si la mascota ya fue marcada como `'Adoptada'` o la solicitud no pertenece al usuario, bloquea la acción con mensaje de error.

### RF14 - Aprobar o rechazar solicitud (evaluar_solicitud)
* **Descripción:** Permite al publicador decidir sobre una solicitud de adopción recibida.
* **Flujo principal:**
  1. El publicador recibe `id_solicitud:HASH`, valida la firma y revisa las respuestas del adoptante.
  2. Presiona "Aprobar" o "Rechazar" (ingresando un motivo si rechaza).
  3. El controlador actualiza el campo `estado_solicitud` en Supabase y notifica el resultado al adoptante.

### RF15 - Programar cita o visita (programar_cita)
* **Descripción:** Permite coordinar un encuentro en persona para conocer a la mascota.
* **Flujo principal:**
  1. Ante una solicitud aprobada, el publicador propone fecha, hora y lugar de encuentro.
  2. El sistema notifica al adoptante y registra la fecha de la cita vinculada a la solicitud.

### RF16 - Mensajería segura entre adoptante y publicador (mensajeria_solicitud)
* **Descripción:** Permite intercambiar mensajes acotados a una solicitud de adopción activa sin exponer datos personales sensibles ni identificadores numéricos en claro.
* **Flujo principal:**
  1. El adoptante o el publicador dueño de la mascota accede desde `lista_solicitudes` mediante `id_solicitud:HASH`.
  2. El controlador valida sesión activa, rol autorizado y que el usuario sea parte de la solicitud.
  3. Muestra el historial de mensajes ordenado cronológicamente y permite enviar un nuevo mensaje de texto validado contra XSS.
  4. Registra el mensaje con fecha y hora, marcándolo como no leído para la contraparte.
* **Flujo alternativo (Error):**
  1. Si el HASH es inválido o el mensaje está vacío, rechaza la operación sin consultar datos.

---

## 7. Módulo 4: Seguimiento Post-Adopción y Bienestar Animal

### RF17 - Subir evidencia y fotos de seguimiento (subir_seguimiento)
* **Descripción:** Permite al adoptante enviar fotos y reportes periódicos para comprobar el buen estado de la mascota adoptada.
* **Flujo principal:**
  1. El adoptante ingresa a sus adopciones activas y selecciona "Enviar Reporte Mensual" pasando `id_mascota:HASH`.
  2. Adjunta una fotografía actual de la mascota y una descripción de su estado de salud y cuidados.
  3. El controlador valida la imagen, la almacena en `static/fotos/` y guarda el registro en la tabla `seguimientos` con la fecha actual y `alerta_maltrato = false`.
* **Flujo alternativo:**
  1. Si falta la fotografía o la descripción, el sistema no permite el envío y solicita completar la información.

### RF18 - Auditar seguimiento y atender alertas de maltrato (auditar_seguimiento)
* **Descripción:** Permite al publicador y al administrador supervisar el historial de evidencias fotográficas, registrar alertas por descuido o maltrato y documentar acciones de intervención y rescate. *(Unifica la detección de maltrato y la gestión del caso de intervención).*
* **Flujo principal:**
  1. El publicador o administrador consulta el historial de reportes de una mascota mediante `id_mascota:HASH` o `id_seguimiento:HASH`.
  2. Si la fotografía o los comentarios evidencian descuido, abandono o lesiones, se presiona "Activar Alerta de Maltrato", actualizando `alerta_maltrato = true`.
  3. El administrador revisa el expediente completo y registra el dictamen de intervención (`'En Inspección'`, `'Rescatado'` o `'Falsa Alarma'`), guardando notas de auditoría y, si procede, bloqueando temporalmente la cuenta del adoptante responsable.
* **Flujo alternativo (Error):**
  1. Si un usuario no autorizado o con HASH inválido intenta modificar la alerta, deniega el acceso y registra el evento en `logging.getLogger(__name__)`.

### RF19 - Notificar falta de seguimiento mensual (notificar_seguimiento)
* **Descripción:** Tarea periódica de supervisión que detecta adopciones sin reporte reciente.
* **Flujo principal:**
  1. El sistema ejecuta una revisión automática calculando los días transcurridos desde el último reporte registrado en `seguimientos` (o desde la fecha de adopción si es el primero).
  2. Si han transcurrido más de 30 días naturales sin evidencia fotográfica, genera una notificación de advertencia en la cuenta del adoptante responsable.
  3. El plazo de 30 días se reinicia automáticamente cuando el adoptante sube un nuevo reporte válido.

---

## 8. Módulo 5: Administración y Moderación del Sistema

### RF20 - Moderar y dictaminar cuentas de usuarios y refugios (moderar_cuentas)
* **Descripción:** Permite al administrador revisar solicitudes de alta de nuevos refugios, emitir dictámenes de aprobación o rechazo, así como suspender o reactivar cuentas por infracciones. *(Unifica la aprobación de refugios y la moderación de cuentas de usuario).*
* **Flujo principal:**
  1. El administrador consulta en el panel administrativo el listado de usuarios y refugios filtrados por estado (`'Pendiente'`, `'Activo'`, `'Suspendido'`) pasando `id_usuario:HASH`.
  2. **Dictamen de refugios:** Ante cuentas de refugio `'Pendiente'`, revisa documentación y selecciona "Aprobar" (pasa a `'Activo'`) o "Rechazar" (con motivo obligatorio).
  3. **Moderación de cuentas:** Ante infracciones o sospechas fundadas, selecciona "Suspender cuenta" (con motivo obligatorio), lo cual revoca inmediatamente sus tokens en `sesiones_abiertas` de Supabase, o "Reactivar cuenta".
  4. El sistema registra el administrador responsable, la fecha del dictamen y notifica al usuario por correo electrónico.
* **Flujo alternativo (Error):**
  1. Si se omite el motivo obligatorio, el HASH es inválido o el administrador intenta suspender su propia cuenta, el sistema rechaza la operación y muestra el mensaje correspondiente.
