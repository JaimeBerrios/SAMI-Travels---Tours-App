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
└── db.sqlite3                 # Base de datos SQLite actual
```

## Tecnologías

- **Python 3.11** en la imagen de producción.
- **Django 4.2+** (limitado a versiones anteriores a Django 5.0).
- **SQLite** para desarrollo local y **MySQL 8+** para producción.
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

### 4. Aplicar las migraciones

```bash
python manage.py migrate
```

Si se necesita acceso a `/admin/` o `/panel-interno/`, crear un superusuario:

```bash
python manage.py createsuperuser
```

### 5. Recolectar los archivos estáticos

```bash
python manage.py collectstatic
```

Django solicitará confirmación si el directorio `staticfiles/` ya contiene archivos. Para omitir la confirmación puede utilizarse:

```bash
python manage.py collectstatic --noinput
```

### 6. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en <http://127.0.0.1:8000/>. El panel administrativo se encuentra en <http://127.0.0.1:8000/admin/>.

Para detener el servidor, presionar:

```text
Ctrl + C
```

### 7. Desactivar el entorno virtual

```bash
deactivate
```

## Variables de entorno

La configuración actual reconoce estas variables:

| Variable | Descripción | Valor predeterminado |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave criptográfica de Django. Debe ser larga, aleatoria y privada en producción. | Clave insegura únicamente para desarrollo |
| `DJANGO_DEBUG` | Activa o desactiva el modo de depuración (`True`/`False`). | `True` |
| `DB_ENGINE` | Selecciona `sqlite` para desarrollo o `mysql` para producción. | `sqlite` |
| `MYSQL_DATABASE` | Nombre de la base de datos MySQL. | `sami_travels` |
| `MYSQL_USER` | Usuario de MySQL. | `sami_user` |
| `MYSQL_PASSWORD` | Contraseña del usuario de MySQL. | Vacío |
| `MYSQL_HOST` | Host o nombre del contenedor MySQL. | `127.0.0.1` |
| `MYSQL_PORT` | Puerto de MySQL. | `3306` |
| `GOOGLE_CLIENT_ID` | Identificador OAuth de Google. | Vacío |
| `GOOGLE_CLIENT_SECRET` | Secreto OAuth de Google. | Vacío |

> [!IMPORTANT]
> En producción se deben proporcionar una `DJANGO_SECRET_KEY` segura y `DJANGO_DEBUG=False`. Nunca se deben almacenar secretos reales en Git.

El dominio de producción configurado en `ALLOWED_HOSTS` es `samitravelsytours.jaimeberrios.com`.

## Guía de despliegue en producción

La aplicación se despliega en un Droplet de DigitalOcean con Ubuntu 24.04 LTS (`68.183.122.81`). Caddy publica `samitravelsytours.jaimeberrios.com`, gestiona HTTPS automáticamente y se comunica con Gunicorn mediante la red Docker compartida `web_network`.

### 1. Publicar los cambios desde el equipo de desarrollo

Antes de actualizar el servidor, compilar y verificar el proyecto:

```bash
python manage.py tailwind build
python manage.py check
git status
git add .
git commit -m "Actualizar Sami Travels & Tours"
git push origin main
```

### 2. Conectarse al servidor y entrar al proyecto

```bash
ssh root@68.183.122.81
cd /var/www/sami_app
```

Si se utiliza un usuario administrativo diferente de `root`, sustituirlo en el comando SSH.

### 3. Descargar el código publicado

```bash
git status --short
git pull --ff-only origin main
```

`git pull --ff-only` evita crear un *merge commit* accidental en producción. Si `git status --short` muestra cambios locales inesperados, detener el despliegue y revisarlos antes de continuar.

### 4. Verificar configuración y red Docker

El archivo `/var/www/sami_app/.env.production` debe existir únicamente en el servidor y no debe almacenarse en Git:

```dotenv
DJANGO_SECRET_KEY=REEMPLAZAR_POR_UNA_CLAVE_SEGURA
DJANGO_DEBUG=False
DB_ENGINE=mysql
MYSQL_DATABASE=sami_travels
MYSQL_USER=sami_user
MYSQL_PASSWORD=REEMPLAZAR_POR_UNA_CONTRASENA_SEGURA
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_CONN_MAX_AGE=60
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ACCOUNT_EMAIL_VERIFICATION=none
```

Comprobar que el archivo y la red existan:

```bash
test -f .env.production
docker network inspect web_network >/dev/null
```

`MYSQL_HOST` debe coincidir con el nombre o alias del contenedor MySQL conectado a `web_network`.

### 5. Reconstruir la imagen corporativa

```bash
docker build --pull -t sami-image:latest .
```

El `Dockerfile` multietapa instala las dependencias npm, compila Tailwind y Font Awesome, instala Python/MySQL/WeasyPrint, ejecuta `collectstatic` y configura Gunicorn en el puerto `8000`.

### 6. Aplicar las migraciones de MySQL

Ejecutar las migraciones con un contenedor temporal antes de reemplazar la aplicación activa:

```bash
docker run --rm \
  --network web_network \
  --env-file .env.production \
  sami-image:latest \
  python manage.py migrate --noinput
```

Si la migración falla, no detener el contenedor que está atendiendo producción. Corregir primero la conexión, las credenciales o la migración.

### 7. Recrear el contenedor de Django

```bash
docker stop sami_container
docker rm sami_container
docker run -d \
  --name sami_container \
  --network web_network \
  --restart unless-stopped \
  --env-file .env.production \
  sami-image:latest
```

Gunicorn escucha en `sami_container:8000` dentro de la red Docker. No es necesario publicar el puerto con `-p` porque Caddy accede al contenedor por `web_network`.

### 8. Verificar Django antes de recargar Caddy

```bash
docker ps --filter name=sami_container
docker logs --tail 100 sami_container
docker exec sami_container python manage.py check --deploy
```

Comprobar desde el propio servidor que Gunicorn responda a través de la red compartida:

```bash
docker run --rm --network web_network curlimages/curl:latest \
  --fail --silent --show-error \
  -H "Host: samitravelsytours.jaimeberrios.com" \
  http://sami_container:8000/ >/dev/null
```

### 9. Validar y recargar Caddy

Validar primero la configuración activa:

```bash
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
```

Si la validación termina correctamente, forzar una recarga limpia:

```bash
docker exec -w /etc/caddy caddy caddy reload --force
```

### 10. Verificación externa

```bash
curl --fail --silent --show-error \
  -o /dev/null \
  -w "HTTP %{http_code}\n" \
  https://samitravelsytours.jaimeberrios.com/

docker logs --tail 100 sami_container
docker logs --tail 100 caddy
```

El resultado esperado es `HTTP 200`. Revisar también el portal, `/accounts/login/`, `/admin/` y la carga de los archivos estáticos desde un navegador.

### Secuencia compacta de actualización

Después de verificar `.env.production`, esta es la secuencia habitual completa dentro de `/var/www/sami_app`:

```bash
git pull --ff-only origin main
docker network inspect web_network >/dev/null
docker build --pull -t sami-image:latest .
docker run --rm --network web_network --env-file .env.production sami-image:latest python manage.py migrate --noinput
docker stop sami_container
docker rm sami_container
docker run -d --name sami_container --network web_network --restart unless-stopped --env-file .env.production sami-image:latest
docker logs --tail 100 sami_container
docker exec sami_container python manage.py check --deploy
docker exec -w /etc/caddy caddy caddy validate --config /etc/caddy/Caddyfile
docker exec -w /etc/caddy caddy caddy reload --force
curl --fail --silent --show-error -o /dev/null -w "HTTP %{http_code}\n" https://samitravelsytours.jaimeberrios.com/
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
