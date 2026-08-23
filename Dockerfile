FROM node:20-slim AS frontend

WORKDIR /theme/static_src

COPY theme/static_src/package.json theme/static_src/package-lock.json ./
RUN npm ci

COPY theme/static_src/ ./
RUN npm run build


FROM python:3.11-slim AS application

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usa los artefactos frontend generados en Linux, no los del equipo local.
COPY --from=frontend /theme/static /app/theme/static

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sami_project.wsgi:application"]
