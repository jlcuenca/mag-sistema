"""
Migrar datos de SQLite local a Cloud SQL (PostgreSQL).
v2 — DROP + RECREATE approach (evita problemas de FK y permisos)

Uso:
    set DATABASE_URL=postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema
    python scripts/migrar_a_cloudsql.py
"""
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine, text, inspect, Boolean
from sqlalchemy.orm import sessionmaker

# ── Configuración ──────────────────────────────────────
SQLITE_PATH = os.path.join(BASE_DIR, "sistema", "data", "mag.db")
PG_URL = os.getenv("DATABASE_URL")

if not PG_URL:
    print("❌ Falta DATABASE_URL. Ejemplo:")
    print('   set DATABASE_URL=postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema')
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f"❌ SQLite no encontrado: {SQLITE_PATH}")
    sys.exit(1)

from api.database import Base

# ── Engines ──────────────────────────────────────────────
sqlite_engine = create_engine(
    f"sqlite:///{SQLITE_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
pg_engine = create_engine(
    PG_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

SqliteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)

BATCH_SIZE = 2000


def migrate_table(table_name, sqlite_sess, pg_sess):
    """Migra una tabla completa de SQLite a PostgreSQL."""
    count = sqlite_sess.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    if count == 0:
        print(f"   ⏭️  {table_name}: vacía, skip")
        return 0

    # Detectar columnas Boolean del modelo
    bool_cols = set()
    if table_name in Base.metadata.tables:
        table_obj = Base.metadata.tables[table_name]
        for col in table_obj.columns:
            if isinstance(col.type, Boolean):
                bool_cols.add(col.name)

    rows = sqlite_sess.execute(text(f"SELECT * FROM {table_name}")).fetchall()
    cols = sqlite_sess.execute(text(f"SELECT * FROM {table_name} LIMIT 1")).keys()
    col_names = list(cols)

    # Insert batch
    placeholders = ", ".join([f":{c}" for c in col_names])
    col_list = ", ".join([f'"{c}"' for c in col_names])
    insert_sql = f'INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})'

    batch = []
    migrated = 0

    for row in rows:
        row_dict = dict(zip(col_names, row))
        # Convertir integers a booleans para PostgreSQL
        for bc in bool_cols:
            if bc in row_dict and row_dict[bc] is not None:
                row_dict[bc] = bool(row_dict[bc])
        batch.append(row_dict)
        migrated += 1

        if len(batch) >= BATCH_SIZE:
            pg_sess.execute(text(insert_sql), batch)
            pg_sess.flush()
            print(f"   ⏳ {table_name}: {migrated:,}/{count:,}...", end="\r")
            batch = []

    if batch:
        pg_sess.execute(text(insert_sql), batch)

    # Reset sequence
    try:
        max_id = pg_sess.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar()
        if max_id:
            pg_sess.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), :max_id, true)"
            ), {"max_id": max_id})
    except Exception:
        pass

    pg_sess.flush()
    print(f"   ✅ {table_name}: {migrated:,} registros migrados" + " " * 20)
    return migrated


def main():
    print("=" * 60)
    print("🚀 MIGRACIÓN SQLite → Cloud SQL (PostgreSQL) v2")
    print("=" * 60)
    print(f"   SQLite: {SQLITE_PATH}")
    pg_display = PG_URL.split("@")[1] if "@" in PG_URL else PG_URL
    print(f"   PostgreSQL: {pg_display}")
    print()

    # Verificar conexión
    print("🔌 Verificando conexión a Cloud SQL...")
    try:
        with pg_engine.connect() as conn:
            ver = conn.execute(text("SELECT version()")).scalar()
            print(f"   ✅ Conectado: {ver[:60]}...")
    except Exception as e:
        print(f"   ❌ No se pudo conectar: {e}")
        sys.exit(1)

    # DROP ALL + RECREATE (manera limpia de evitar FK issues)
    print("\n🗑️  Eliminando tablas existentes (DROP CASCADE)...")
    Base.metadata.drop_all(bind=pg_engine)
    print("   ✅ Tablas eliminadas")

    print("📦 Recreando tablas limpias...")
    Base.metadata.create_all(bind=pg_engine)
    print("   ✅ Tablas creadas")

    # Tablas en SQLite
    sqlite_tables = inspect(sqlite_engine).get_table_names()
    print(f"\n📋 Tablas en SQLite: {len(sqlite_tables)}")

    # Orden de migración (por dependencias FK)
    TABLAS_ORDEN = [
        "segmentos",
        "gestiones_comerciales",
        "agentes",
        "productos",
        "contratantes",
        "polizas",
        "recibos",
        "pagos",
        "indicadores_axa",
        "conciliaciones",
        "presupuestos",
        "metas",
        "importaciones",
        "solicitudes",
        "distribuciones_comision",
        "etapas_solicitudes",
        "configuraciones",
    ]

    sqlite_sess = SqliteSession()
    pg_sess = PgSession()

    start = time.time()
    total_migrated = 0

    try:
        print("\n🔄 Migrando datos...")
        for table in TABLAS_ORDEN:
            if table in sqlite_tables:
                try:
                    n = migrate_table(table, sqlite_sess, pg_sess)
                    total_migrated += n
                    pg_sess.commit()  # Commit por tabla para evitar rollback masivo
                except Exception as e:
                    print(f"   ❌ Error en {table}: {str(e)[:120]}")
                    pg_sess.rollback()
                    continue

        elapsed = time.time() - start

        print(f"\n{'=' * 60}")
        print(f"✅ MIGRACIÓN COMPLETADA")
        print(f"{'=' * 60}")
        print(f"   Total registros: {total_migrated:,}")
        print(f"   Tiempo: {elapsed:.1f}s")

        # Verificación
        print(f"\n📊 Verificación:")
        for table in TABLAS_ORDEN:
            if table in sqlite_tables:
                try:
                    sc = sqlite_sess.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    pc = pg_sess.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    st = "✅" if sc == pc else "⚠️"
                    print(f"   {st} {table:30s} SQLite:{sc:>8,}  PG:{pc:>8,}")
                except Exception:
                    pass

        print(f"\n🎉 ¡Migración lista! Configura DATABASE_URL en Cloud Run para usar PostgreSQL.")

    except Exception as e:
        pg_sess.rollback()
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sqlite_sess.close()
        pg_sess.close()


if __name__ == "__main__":
    main()
