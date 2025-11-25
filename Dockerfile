# =====================================================
# ETAPA 1 — BUILDER: instala dependencias
# =====================================================
FROM python:3.11-slim AS builder

WORKDIR /usr/src/app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# =====================================================
# ETAPA 2 — TESTER: ejecuta los tests automáticamente
# =====================================================
FROM builder AS tester

# Indicar que estamos en modo testing para que app.py no haga wait_for_db/init_db
ENV FLASK_ENV=testing

# Ejecutar tests
RUN pytest -v

# =====================================================
# ETAPA 3 — FINAL: imagen limpia para producción
# =====================================================
FROM python:3.11-slim

WORKDIR /usr/src/app

# Dependencias mínimas necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
