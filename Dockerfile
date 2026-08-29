FROM node:20-slim AS frontend

WORKDIR /app

# Tailwind se compila en cada build para que la imagen nunca dependa de un
# styles.css obsoleto generado en el equipo de desarrollo.
COPY package.json package-lock.json ./
RUN npm ci

COPY theme/src/ ./theme/src/
COPY theme/static_src/tailwind.config.js ./theme/static_src/tailwind.config.js
COPY theme/templates/ ./theme/templates/
COPY core/templates/ ./core/templates/
COPY core/*.py ./core/
COPY sami_admin/templates/ ./sami_admin/templates/
COPY sami_admin/*.py ./sami_admin/

RUN npm run build:css


FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias para mysqlclient y WeasyPrint (Pango/Harfbuzz).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# La compilación de la etapa frontend prevalece sobre cualquier copia local.
COPY --from=frontend /app/theme/static/css/dist/styles.css /app/theme/static/css/dist/styles.css

RUN DJANGO_SECRET_KEY=dummy-key-for-build MYSQL_DATABASE=dummy MYSQL_USER=dummy MYSQL_PASSWORD=dummy MYSQL_HOST=dummy python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sami_project.wsgi:application"]
