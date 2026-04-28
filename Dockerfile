# Dockerfile — MAG Sistema Backend (FastAPI)
# Proyecto GCP: magia-mag
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema (psycopg2 + Oracle Client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libaio1 wget unzip && \
    mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/211000/instantclient-basiclite-linux.x64-21.1.0.0.0.zip && \
    unzip instantclient-basiclite-linux.x64-21.1.0.0.0.zip && \
    rm -f instantclient-basiclite-linux.x64-21.1.0.0.0.zip && \
    rm -rf /var/lib/apt/lists/*

ENV ORACLE_CLIENT_PATH=/opt/oracle/instantclient_21_1
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1

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
