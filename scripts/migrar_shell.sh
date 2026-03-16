#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Migración SQLite → Cloud SQL desde Cloud Shell
# Ejecutar desde Google Cloud Shell (mucho más rápido que local)
#
# Uso:
#   1. Abre Cloud Shell: https://console.cloud.google.com/cloudshell
#   2. Copia este script: gsutil cp gs://mag-sistema-data/migrar_shell.sh .
#   3. chmod +x migrar_shell.sh && ./migrar_shell.sh
# ═══════════════════════════════════════════════════════════════

set -e

PROJECT="magia-mag"
INSTANCE="mag-db"
DB_NAME="mag_sistema"
DB_USER="mag_user"
DB_PASS="MagS1st3ma2026Gcp"
REGION="us-central1"

echo "═══════════════════════════════════════════════════════════"
echo "🚀 Migración SQLite → Cloud SQL (PostgreSQL)"
echo "═══════════════════════════════════════════════════════════"

# 1. Descargar SQLite desde GCS
echo ""
echo "📥 Descargando mag.db desde GCS..."
gsutil cp gs://mag-sistema-data/mag.db /tmp/mag.db
ls -lh /tmp/mag.db

# 2. Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install --quiet sqlalchemy psycopg2-binary pandas 2>/dev/null

# 3. Obtener IP privada de Cloud SQL (o usar proxy)
echo ""
echo "🔌 Configurando conexión a Cloud SQL..."

# Usar Cloud SQL Auth Proxy
if [ ! -f /tmp/cloud-sql-proxy ]; then
    echo "   Descargando Cloud SQL Auth Proxy..."
    curl -o /tmp/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.3/cloud-sql-proxy.linux.amd64
    chmod +x /tmp/cloud-sql-proxy
fi

# Iniciar proxy en background
echo "   Iniciando proxy..."
/tmp/cloud-sql-proxy --port 5432 ${PROJECT}:${REGION}:${INSTANCE} &
PROXY_PID=$!
sleep 3

export DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}"

# 4. Ejecutar migración con Python
echo ""
echo "🔄 Ejecutando migración..."

python3 << 'PYTHON_SCRIPT'
import os
import sys
import time
from sqlalchemy import create_engine, text, inspect, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

SQLITE_PATH = "/tmp/mag.db"
PG_URL = os.environ["DATABASE_URL"]

sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})
pg_engine = create_engine(PG_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)

SqliteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)

# Verificar conexión
with pg_engine.connect() as conn:
    ver = conn.execute(text("SELECT version()")).scalar()
    print(f"   ✅ Conectado a PostgreSQL: {ver[:60]}")

# Obtener tablas y estructura de SQLite
sqlite_tables = inspect(sqlite_engine).get_table_names()
print(f"   📋 Tablas en SQLite: {len(sqlite_tables)} — {', '.join(sqlite_tables)}")

# Clonar repo para obtener modelos
import subprocess
subprocess.run(["pip", "install", "--quiet", "pydantic", "fastapi", "httpx", "python-dateutil", "openpyxl", "xlsxwriter", "pdfplumber", "python-multipart"], check=True)

# Clonar el repo para tener los modelos
if not os.path.exists("/tmp/mag-sistema"):
    subprocess.run(["git", "clone", "--depth=1", "https://github.com/jlcuenca/mag-sistema.git", "/tmp/mag-sistema"], check=True)

sys.path.insert(0, "/tmp/mag-sistema")
os.chdir("/tmp/mag-sistema")
from api.database import Base

# DROP y CREATE tablas
print("\n🗑️  DROP ALL tables...")
Base.metadata.drop_all(bind=pg_engine)
print("📦 CREATE ALL tables...")
Base.metadata.create_all(bind=pg_engine)

# Detectar columnas Boolean
bool_cols_map = {}
for tname, tobj in Base.metadata.tables.items():
    bcols = set()
    for col in tobj.columns:
        if isinstance(col.type, Boolean):
            bcols.add(col.name)
    if bcols:
        bool_cols_map[tname] = bcols

BATCH_SIZE = 5000
TABLAS_ORDEN = [
    "segmentos", "gestiones_comerciales", "agentes", "productos",
    "contratantes", "polizas", "recibos", "pagos",
    "indicadores_axa", "conciliaciones", "presupuestos", "metas",
    "importaciones", "solicitudes", "distribuciones_comision",
    "etapas_solicitudes", "configuraciones",
]

sqlite_sess = SqliteSession()
pg_sess = PgSession()
start = time.time()
total = 0

print("\n🔄 Migrando datos...")
for table in TABLAS_ORDEN:
    if table not in sqlite_tables:
        continue
    count = sqlite_sess.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    if count == 0:
        print(f"   ⏭️  {table}: vacía")
        continue

    rows = sqlite_sess.execute(text(f"SELECT * FROM {table}")).fetchall()
    col_names = list(sqlite_sess.execute(text(f"SELECT * FROM {table} LIMIT 1")).keys())
    bool_cols = bool_cols_map.get(table, set())

    placeholders = ", ".join([f":{c}" for c in col_names])
    col_list = ", ".join([f'"{c}"' for c in col_names])
    insert_sql = f'INSERT INTO {table} ({col_list}) VALUES ({placeholders})'

    batch = []
    migrated = 0
    for row in rows:
        rd = dict(zip(col_names, row))
        for bc in bool_cols:
            if bc in rd and rd[bc] is not None:
                rd[bc] = bool(rd[bc])
        batch.append(rd)
        migrated += 1
        if len(batch) >= BATCH_SIZE:
            pg_sess.execute(text(insert_sql), batch)
            pg_sess.flush()
            print(f"   ⏳ {table}: {migrated:,}/{count:,}...", end="\r")
            batch = []

    if batch:
        pg_sess.execute(text(insert_sql), batch)

    # Reset sequence
    try:
        max_id = pg_sess.execute(text(f"SELECT MAX(id) FROM {table}")).scalar()
        if max_id:
            pg_sess.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), :max_id, true)"), {"max_id": max_id})
    except:
        pass

    pg_sess.commit()
    total += migrated
    print(f"   ✅ {table}: {migrated:,} registros" + " " * 30)

elapsed = time.time() - start
print(f"\n{'='*60}")
print(f"✅ MIGRACIÓN COMPLETADA — {total:,} registros en {elapsed:.1f}s")
print(f"{'='*60}")

# Verificación
print("\n📊 Verificación:")
for table in TABLAS_ORDEN:
    if table in sqlite_tables:
        try:
            sc = sqlite_sess.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            pc = pg_sess.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            st = "✅" if sc == pc else "⚠️"
            print(f"   {st} {table:30s} SQLite:{sc:>8,}  PG:{pc:>8,}")
        except:
            pass

sqlite_sess.close()
pg_sess.close()
PYTHON_SCRIPT

# 5. Cleanup
echo ""
echo "🧹 Limpiando..."
kill $PROXY_PID 2>/dev/null || true

echo ""
echo "🎉 ¡Migración completada desde Cloud Shell!"
echo "   Ahora despliega el backend con: gcloud run deploy mag-api ..."
