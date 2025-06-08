# Dockerfile limpio y corregido para FastAPI + Cloud Run + MySQL
FROM python:3.13-alpine

# No generar archivos .pyc y permitir logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar e interactuar con MySQL
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    mariadb-dev \
    build-base \
    openssl-dev \
    && pip install --upgrade pip

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Asegurar que se copien correctamente las plantillas HTML
COPY ./templates /app/templates

# Crear un usuario sin privilegios y cambiar permisos por seguridad
RUN adduser -D appuser \
    && chown -R appuser /app
USER appuser

# Puerto de entrada requerido por Cloud Run
EXPOSE 8080

# Variables necesarias para la conexión con Cloud SQL vía socket
ENV DB_SOCKET_PATH=/cloudsql
ENV CLOUD_SQL_CONNECTION_NAME=capirulo:us-central1:fastapi-mysql

# Comando para lanzar FastAPI con Uvicorn en el contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
