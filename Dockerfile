# Dockerfile — MAG Sistema Backend (FastAPI)
# Proyecto GCP: magia-mag
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY main.py .
COPY api/ ./api/
COPY scripts/ ./scripts/

# Puerto (Cloud Run inyecta $PORT)
ENV PORT=8080
EXPOSE 8080

# Comando de inicio
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
