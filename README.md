# Sami Travels & Tours

Aplicación web desarrollada con Django para **Sami Travels & Tours**, como parte de un proyecto de servicio social universitario. El sistema ofrece un portal público para presentar los servicios de la agencia y recibir solicitudes de cotización, además de espacios protegidos para la gestión interna.

## Descripción del proyecto

La aplicación está compuesta por tres áreas principales:

- **Portal público (`/`)**: página principal de la agencia y formulario provisional para solicitudes de cotización.
- **Panel interno (`/panel-interno/`)**: espacio de trabajo reservado para usuarios del equipo con permisos de *staff*.
- **Administración de Django (`/admin/`)**: interfaz administrativa para usuarios autorizados.

El proyecto utiliza la aplicación Django `core` para las vistas, rutas, plantillas y recursos estáticos de la interfaz. La configuración general, así como los puntos de entrada WSGI y ASGI, se encuentran en `sami_project`.

## Estructura del proyecto

```text
SAMI/
├── core/
│   ├── static/core/css/       # Estilos propios de la aplicación
│   ├── templates/core/        # Plantillas del portal y panel interno
│   ├── apps.py
│   ├── urls.py                # Rutas de la aplicación core
│   └── views.py               # Vistas públicas y protegidas
├── sami_project/
│   ├── settings.py            # Configuración de Django
│   ├── urls.py                # Enrutamiento principal
│   ├── asgi.py
│   └── wsgi.py                # Punto de entrada utilizado por Gunicorn
├── staticfiles/               # Archivos recopilados por collectstatic
├── .dockerignore
├── Dockerfile
├── manage.py
├── requirements.txt
└── db.sqlite3                 # Base SQLite heredada (uso local opcional)
```

## Tecnologías

- **Python 3.11** en la imagen de producción.
- **Django 4.2+** (limitado a versiones anteriores a Django 5.0).
- **MySQL 8.0** como base de datos principal; SQLite queda disponible para tareas locales opcionales.
- **Gunicorn** como servidor WSGI de producción.
- **Docker** para construir y ejecutar la aplicación de forma aislada.
- **Caddy Server** como proxy inverso, encargado de publicar la aplicación y administrar automáticamente los certificados SSL/TLS mediante Let's Encrypt.
- **DigitalOcean** como infraestructura del servidor de producción.

### Flujo de producción

```text
Cliente HTTPS
    │
    ▼
Caddy (SSL automático / proxy inverso)
    │  red Docker: web_network
    ▼
sami_container (Gunicorn :8000)
    │
    ▼
Django / MySQL
```

## Requisitos previos

Para trabajar localmente se necesita:

- Git.
- Python 3.11 o una versión compatible con Django 4.2.
- `pip` y el módulo `venv`.
- Node.js y npm para compilar Tailwind CSS cuando cambien estilos o plantillas.
- Conexión a Internet para cargar Anime.js, Font Awesome y Google Maps durante el desarrollo.
- Docker, únicamente si se desea probar la imagen de producción.

## Guía de ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/JaimeBerrios/SAMI-Travels---Tours-App.git
cd SAMI-Travels---Tours-App
```

### 2. Crear y activar el entorno virtual

Crear el entorno:

```bash
python -m venv venv
```

Activarlo en Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Activarlo en Linux o macOS:

```bash
source venv/bin/activate
```

Al activarse correctamente, la terminal normalmente mostrará `(venv)` antes del prompt.

### 3. Instalar las dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Instalar también las dependencias frontend:

```bash
cd theme/static_src
npm ci
cd ../..
```

### 4. Compilar Tailwind CSS

Generar una vez el CSS minificado:

```bash
npm --prefix theme/static_src run build:tailwind
```

Mientras se trabaja en estilos o plantillas, ejecutar el observador en una segunda terminal:

```bash
npm --prefix theme/static_src run dev
```

El archivo generado que sirve Django es `theme/static/css/dist/styles.css`. Detener el observador con `Ctrl+C`.

### 5. Aplicar las migraciones

```bash
python manage.py migrate
```

Si se necesita acceso a `/admin/` o `/panel-interno/`, crear un superusuario:

```bash
python manage.py createsuperuser
```

### 6. Verificar y ejecutar las pruebas

```bash
python manage.py check
python manage.py test
```

### 7. Recolectar los archivos estáticos (opcional en desarrollo)

```bash
python manage.py collectstatic
```

Django solicitará confirmación si el directorio `staticfiles/` ya contiene archivos. Para omitir la confirmación puede utilizarse:

```bash
python manage.py collectstatic --noinput
```

Con `DEBUG=True`, `runserver` sirve directamente los archivos de cada aplicación, por lo que este paso no es necesario para el uso local habitual. Sí permite comprobar anticipadamente el comportamiento de WhiteNoise.

### 8. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en <http://127.0.0.1:8000/>. El panel administrativo se encuentra en <http://127.0.0.1:8000/admin/>.

Para detener el servidor, presionar:

```text
Ctrl + C
```

El mapa muestra la zona desde la cual se brindan los servicios virtuales; no representa una oficina física abierta al público. Anime.js, Font Awesome y el mapa requieren conexión a Internet.

### 9. Desactivar el entorno virtual

```bash
deactivate
```

## Variables de entorno

La configuración actual reconoce estas variables:

| Variable | Descripción | Valor predeterminado |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave criptográfica de Django. Debe ser larga, aleatoria y privada en producción. | Clave insegura únicamente para desarrollo |
| `DJANGO_DEBUG` | Activa o desactiva el modo de depuración (`True`/`False`). | `True` |
| `DB_ENGINE` | Selecciona `mysql` (principal) o `sqlite` para tareas locales opcionales. | `mysql` |
| `MYSQL_DATABASE` | Nombre de la base de datos MySQL. | `sami_db` |
| `MYSQL_USER` | Usuario de MySQL. | `jaifer08` |
| `MYSQL_PASSWORD` | Contraseña del usuario de MySQL. | Vacío |
| `MYSQL_HOST` | Host o nombre del contenedor MySQL. | `mysql_server` |
| `MYSQL_PORT` | Puerto de MySQL. | `3306` |
| `GOOGLE_CLIENT_ID` | Identificador OAuth de Google. | Vacío |
| `GOOGLE_CLIENT_SECRET` | Secreto OAuth de Google. | Vacío |
| `CONTACT_EMAIL` | Correo mostrado en la página de mantenimiento. | `contacto@samitravelstours.com` |

> [!IMPORTANT]
> En producción se deben proporcionar una `DJANGO_SECRET_KEY` segura y `DJANGO_DEBUG=False`. Nunca se deben almacenar secretos reales en Git.

Los dominios de producción configurados en `ALLOWED_HOSTS` son `samitravelstours.com` y `www.samitravelstours.com`. El dominio anterior se conserva temporalmente por compatibilidad.

## Flujo para actualizar la aplicación

La aplicación se despliega en un Droplet de DigitalOcean con Ubuntu 24.04 LTS (`68.183.122.81`). Caddy publica `samitravelstours.com`, gestiona HTTPS automáticamente y se comunica con Gunicorn mediante la red Docker compartida `web_network`.

### Resumen del flujo de desarrollo y actualización

El ciclo de trabajo comienza en el equipo local. Después de desarrollar y verificar los cambios, guardarlos en el historial de Git y enviarlos a GitHub:

```bash
git add .
git commit -m "Descripción de los cambios"
git push origin main
```

Luego, conectarse al VPS y entrar al directorio de la aplicación:

```bash
ssh root@68.183.122.81
cd /var/www/sami_app
```

Descargar la versión publicada en la rama principal:

```bash
git pull origin main
```

La secuencia directa para reconstruir y recrear el contenedor es:

```bash
docker stop sami_container
docker rm sami_container
docker build -t sami_app_image .
docker run -d --name sami_container --network web_network -p 8000:8000 sami_app_image
docker exec -it sami_container python manage.py collectstatic --noinput
docker restart caddy
```

> [!IMPORTANT]
> La aplicación real utiliza `.env.production`, migraciones y el volumen persistente `sami_static`. Por ello, para una actualización completa y segura se debe seguir la secuencia detallada que aparece a continuación; esta conserva la conexión a MySQL, los secretos y los archivos estáticos compartidos con Caddy.

Los archivos estáticos de producción se guardan en el volumen Docker nombrado `sami_static`:

```text
contenedor temporal (collectstatic) ──► sami_static ◄── sami_container (/app/staticfiles)
                                             └── caddy (/srv/sami_static, solo lectura)
```

Caddy sirve `/static/` directamente. WhiteNoise permanece disponible en Django como respaldo y utiliza el mismo contenido montado en `/app/staticfiles`.

### Parte A: trabajo en el equipo local

#### 1. Actualizar la rama antes de comenzar

Con el entorno virtual activado:

```bash
git switch main
git pull --ff-only origin main
pip install -r requirements.txt
npm --prefix theme/static_src ci
```

#### 2. Implementar y comprobar los cambios

Si se modifican modelos, crear y revisar las migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

Si cambian plantillas, clases o configuración de Tailwind, regenerar el CSS que se guarda en Git:

```bash
npm --prefix theme/static_src run build:tailwind
```

Antes de actualizar el servidor, compilar y verificar el proyecto:

```bash
python manage.py check
python manage.py test
git diff --check
git status
```

Probar visualmente en <http://127.0.0.1:8000/>:

```bash
python manage.py runserver
```

#### 3. Publicar los cambios

Revisar `git diff` antes de crear el commit. Debe incluir `theme/static/css/dist/styles.css` cuando se modificaron clases de Tailwind.

```bash
git diff
git add .
git commit -m "Actualizar Sami Travels & Tours"
git push origin main
```

No subir `.env`, `.env.production`, contraseñas, copias de la base de datos ni el entorno virtual.

### Parte B: actualización en el servidor

#### 4. Conectarse al servidor y entrar al proyecto

```bash
ssh root@68.183.122.81
cd /var/www/sami_app
```

Si se utiliza un usuario administrativo diferente de `root`, sustituirlo en el comando SSH.

#### 5. Descargar el código publicado

```bash
git status --short
git pull --ff-only origin main
```

`git pull --ff-only` evita crear un *merge commit* accidental en producción. Si `git status --short` muestra cambios locales inesperados, detener el despliegue y revisarlos antes de continuar.

#### 6. Verificar configuración y red Docker

El archivo `/var/www/sami_app/.env.production` debe existir únicamente en el servidor y no debe almacenarse en Git:

```dotenv
DJANGO_SECRET_KEY=REEMPLAZAR_POR_UNA_CLAVE_SEGURA
DJANGO_DEBUG=False
DB_ENGINE=mysql
MYSQL_DATABASE=sami_db
MYSQL_USER=jaifer08
MYSQL_PASSWORD=REEMPLAZAR_POR_UNA_CONTRASENA_SEGURA
MYSQL_HOST=mysql_server
MYSQL_PORT=3306
MYSQL_CONN_MAX_AGE=60
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ACCOUNT_EMAIL_VERIFICATION=none
```

Comprobar que el archivo, la red y el volumen de estáticos existan:

```bash
test -f .env.production
docker network inspect web_network >/dev/null
docker volume inspect sami_static >/dev/null 2>&1 || docker volume create sami_static
```

`MYSQL_HOST` debe ser `mysql_server`, el nombre o alias del contenedor MySQL conectado a `web_network`.

#### 7. Reconstruir la imagen de la aplicación

```bash
docker build --pull -t sami-image:latest .
```

El `Dockerfile` instala Python, las bibliotecas nativas de MySQL/WeasyPrint y las dependencias de `requirements.txt`. Después copia el CSS de Tailwind previamente compilado, ejecuta `collectstatic` dentro de la imagen y configura Gunicorn en el puerto `8000`. Node.js no se ejecuta dentro del contenedor actual.

El volumen montado en producción oculta el directorio `staticfiles` incluido en la imagen. Por eso el paso explícito de `collectstatic` contra `sami_static` que aparece más adelante es obligatorio.

#### 8. Aplicar las migraciones de MySQL

Ejecutar las migraciones con un contenedor temporal antes de reemplazar la aplicación activa:

```bash
docker run --rm \
  --network web_network \
  --env-file .env.production \
  sami-image:latest \
  python manage.py migrate --noinput
```

Si la migración falla, no detener el contenedor que está atendiendo producción. Corregir primero la conexión, las credenciales o la migración.

#### 9. Recopilar los archivos estáticos en el volumen compartido

Ejecutar `collectstatic` desde la imagen nueva y montar el volumen en la misma ruta definida por `STATIC_ROOT` (`/app/staticfiles`):

```bash
docker run --rm \
  --network web_network \
  --env-file .env.production \
  --mount source=sami_static,target=/app/staticfiles \
  sami-image:latest \
  python manage.py collectstatic --noinput
```

No utilizar `--clear` durante una actualización normal: Caddy puede estar leyendo el volumen mientras se recopilan los archivos. Los nombres versionados generados por WhiteNoise permiten actualizarlo sin invalidar los recursos que todavía usan clientes con páginas anteriores.

Comprobar que el manifiesto y el CSS se encuentren en el volumen:

```bash
docker run --rm \
  --mount source=sami_static,target=/staticfiles,readonly \
  alpine:3.20 \
  sh -c 'test -f /staticfiles/staticfiles.json && test -d /staticfiles/css/dist'
```

Si este comando falla, no reemplazar aún `sami_container`.

#### 10. Recrear el contenedor de Django

```bash
docker stop sami_container
docker rm sami_container
docker run -d \
  --name sami_container \
  --network web_network \
  --restart unless-stopped \
  --env-file .env.production \
  --mount source=sami_static,target=/app/staticfiles \
  sami-image:latest
```

Gunicorn escucha en `sami_container:8000` dentro de la red Docker. No es necesario publicar el puerto con `-p` porque Caddy accede al contenedor por `web_network`.

#### 11. Verificar Django antes de recargar Caddy

```bash
docker ps --filter name=sami_container
docker logs --tail 100 sami_container
docker exec sami_container python manage.py check --deploy
```

Comprobar desde el propio servidor que Gunicorn responda a través de la red compartida:

```bash
docker run --rm --network web_network curlimages/curl:latest \
  --fail --silent --show-error \
  -H "Host: samitravelstours.com" \
  http://sami_container:8000/ >/dev/null
```

#### 12. Configurar, validar y recargar Caddy

El contenedor `caddy` debe tener el mismo volumen montado en modo de solo lectura:

```text
--mount source=sami_static,target=/srv/sami_static,readonly
```

Este montaje se configura al crear el contenedor de Caddy o en su archivo Compose; no puede agregarse a un contenedor que ya está ejecutándose. Antes de recrear Caddy, conservar sus opciones actuales, redes, puertos y volúmenes de certificados. Confirmar el montaje con:

```bash
docker inspect caddy \
  --format '{{range .Mounts}}{{println .Name "->" .Destination}}{{end}}'
```

El bloque del sitio en `/etc/caddy/Caddyfile` debe dirigir `/static/*` al volumen y el resto a Gunicorn:

```caddyfile
samitravelstours.com, www.samitravelstours.com {
    encode zstd gzip

    handle_path /static/* {
        root * /srv/sami_static
        file_server
    }

    handle {
        reverse_proxy sami_container:8000
    }
}
```

Validar primero la configuración activa:

```bash
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
```

Si la validación termina correctamente, forzar una recarga limpia:

```bash
docker exec -w /etc/caddy caddy caddy reload --force
```

#### 13. Verificación externa

```bash
curl --fail --silent --show-error \
  -o /dev/null \
  -w "HTTP %{http_code}\n" \
  https://samitravelstours.com/

curl --fail --silent --show-error \
  -o /dev/null \
  -w "Static HTTP %{http_code}\n" \
  https://samitravelstours.com/static/css/dist/styles.css

docker logs --tail 100 sami_container
docker logs --tail 100 caddy
```

El resultado esperado es `HTTP 200`. Revisar también el portal, `/accounts/login/`, `/admin/` y la carga de los archivos estáticos desde un navegador.

### Secuencia compacta de actualización

Después de verificar `.env.production`, esta es la secuencia habitual completa dentro de `/var/www/sami_app`:

```bash
git pull --ff-only origin main
docker network inspect web_network >/dev/null
docker volume inspect sami_static >/dev/null 2>&1 || docker volume create sami_static
docker build --pull -t sami-image:latest .
docker run --rm --network web_network --env-file .env.production sami-image:latest python manage.py migrate --noinput
docker run --rm --network web_network --env-file .env.production --mount source=sami_static,target=/app/staticfiles sami-image:latest python manage.py collectstatic --noinput
docker stop sami_container
docker rm sami_container
docker run -d --name sami_container --network web_network --restart unless-stopped --env-file .env.production --mount source=sami_static,target=/app/staticfiles sami-image:latest
docker logs --tail 100 sami_container
docker exec sami_container python manage.py check --deploy
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
docker exec -w /etc/caddy caddy caddy reload --force
curl --fail --silent --show-error -o /dev/null -w "HTTP %{http_code}\n" https://samitravelstours.com/
```

## Comandos útiles

```bash
# Comprobar la configuración de Django
python manage.py check

# Crear nuevas migraciones después de modificar modelos
python manage.py makemigrations

# Aplicar migraciones pendientes
python manage.py migrate

# Ver los registros del contenedor en tiempo real
docker logs -f sami_container

# Reiniciar el contenedor sin reconstruir la imagen
docker restart sami_container
```

## Consideraciones de seguridad y operación

- Mantener `DJANGO_DEBUG=False` en producción.
- Proteger `DJANGO_SECRET_KEY` y cualquier otra credencial mediante variables de entorno o un gestor de secretos.
- Restringir el acceso SSH y mantener actualizados el sistema operativo, Docker y las dependencias.
- Realizar copias de seguridad periódicas de la base de datos.
- Validar las migraciones antes de cada despliegue.
- Revisar los registros de Django, Gunicorn y Caddy después de actualizar la aplicación.

## Contexto académico

Este proyecto fue desarrollado como parte de un servicio social universitario, con el objetivo de aportar una solución digital para la presencia pública y la operación interna de Sami Travels & Tours.
