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
- **SQLite** como base de datos actual.
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
Django / SQLite
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

> [!IMPORTANT]
> En producción se deben proporcionar una `DJANGO_SECRET_KEY` segura y `DJANGO_DEBUG=False`. Nunca se deben almacenar secretos reales en Git.

El dominio de producción configurado en `ALLOWED_HOSTS` es `samitravelsytours.jaimeberrios.com`.

## Guía de despliegue en producción

La infraestructura prevista utiliza un servidor de DigitalOcean, Docker para la aplicación y un contenedor Caddy conectado a la red compartida `web_network`.

### 1. Publicar los cambios en GitHub

Desde el equipo de desarrollo, revisar y enviar los cambios:

```bash
git status
git add .
git commit -m "Descripción breve de los cambios"
git push origin main
```

Si la rama de producción tiene otro nombre, sustituir `main` por la rama correspondiente.

### 2. Conectarse al servidor

```bash
ssh usuario@IP_DEL_SERVIDOR
```

Entrar al directorio de la aplicación:

```bash
cd /var/www/sami_app
```

### 3. Descargar los cambios

```bash
git pull origin main
```

### 4. Reconstruir la imagen Docker

```bash
docker build -t sami-image .
```

Durante la construcción, el `Dockerfile` instala las dependencias y ejecuta `python manage.py collectstatic --noinput`.

### 5. Recrear el contenedor de la aplicación

Detener y eliminar el contenedor anterior, si existe:

```bash
docker stop sami_container
docker rm sami_container
```

Crear el contenedor actualizado y conectarlo a la red compartida:

```bash
docker run -d \
  --name sami_container \
  --network web_network \
  --restart unless-stopped \
  -e DJANGO_DEBUG=False \
  -e DJANGO_SECRET_KEY="REEMPLAZAR_POR_UNA_CLAVE_SEGURA" \
  sami-image
```

La forma mínima del comando, cuando las variables ya se suministran por otro mecanismo, es:

```bash
docker run -d --name sami_container --network web_network --restart unless-stopped sami-image
```

> [!WARNING]
> El contenedor actual utiliza SQLite dentro de su sistema de archivos. Al eliminarlo también se elimina cualquier dato escrito dentro del contenedor. Antes de usar datos reales, debe configurarse almacenamiento persistente mediante un volumen o migrarse a una base de datos externa.

### 6. Recargar Caddy

Forzar una recarga limpia de la configuración de Caddy:

```bash
docker exec -w /etc/caddy caddy caddy reload --force
```

Caddy actúa como proxy inverso hacia `sami_container:8000` dentro de `web_network` y gestiona automáticamente HTTPS con certificados de Let's Encrypt.

### 7. Verificar el despliegue

Comprobar que los contenedores están en ejecución:

```bash
docker ps
```

Consultar los registros de la aplicación:

```bash
docker logs --tail 100 sami_container
```

Finalmente, visitar <https://samitravelsytours.jaimeberrios.com> y comprobar el portal público, el inicio de sesión administrativo y la carga de archivos estáticos.

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
