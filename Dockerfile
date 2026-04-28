# Dockerfile — MAG Sistema Backend (FastAPI)
# Proyecto GCP: magia-mag
FROM python:3.12-slim

WORKDIR /app

# 1. Dependencias del sistema (psycopg2 + Oracle Client)
# libaio1 es crítica para el funcionamiento del cliente de Oracle.
# libnsl2 es necesaria en Debian Bookworm para compatibilidad con versiones anteriores.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libaio1 libnsl2 wget unzip && \
    mkdir -p /opt/oracle && \
    wget --no-check-certificate https://download.oracle.com/otn_software/linux/instantclient/2121000/instantclient-basiclite-linux.x64-21.21.0.0.0dbru.zip -O /opt/oracle/oracle.zip && \
    unzip /opt/oracle/oracle.zip -d /opt/oracle && \
    rm -f /opt/oracle/oracle.zip && \
    echo /opt/oracle/instantclient_21_21 > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig && \
    rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno para el modo Thick
ENV ORACLE_CLIENT_PATH=/opt/oracle/instantclient_21_21
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_21

# 2. Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Código de la aplicación
COPY main.py .
COPY api/ ./api/
COPY scripts/ ./scripts/

# Puerto (Cloud Run inyecta $PORT)
ENV PORT=8080
EXPOSE 8080

# Comando de inicio
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
