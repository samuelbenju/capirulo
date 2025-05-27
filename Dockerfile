# Dockerfile limpio y corregido para FastAPI + Cloud Run + MySQL
FROM python:3.13-alpine

# Evitar archivos .pyc y permitir logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
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

# Copiar código fuente
COPY . .

# Crear usuario sin privilegios y cambiar permisos
RUN adduser -D appuser \
    && chown -R appuser /app
USER appuser

# Exponer puerto requerido por Cloud Run
EXPOSE 8080

ENV DB_SOCKET_PATH=/cloudsql
ENV CLOUD_SQL_CONNECTION_NAME=capirulo:us-central1:fastapi-mysql

# Comando para ejecutar FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
