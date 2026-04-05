"""
Migración de BD para Refactor v2.0 — Solicitud-Céntrico
========================================================
Agrega columnas nuevas a tablas existentes SIN destruir datos.
Usa ALTER TABLE para SQLite (compatible con PostgreSQL).

Uso:
    python scripts/migrar_solicitud_centrico.py
"""
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text, inspect
from api.database import SessionLocal, engine, Base


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Verifica si una columna ya existe en la tabla."""
    try:
        columns = [c["name"] for c in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def table_exists(inspector, table_name: str) -> bool:
    """Verifica si una tabla existe."""
    return table_name in inspector.get_table_names()


def main():
    print("=" * 60)
    print("🔧 MIGRACIÓN v2.0 — Solicitud-Céntrico")
    print("=" * 60)
    start = time.time()

    db = SessionLocal()
    inspector = inspect(engine)

    try:
        # ══════════════════════════════════════════════════════════
        # 1. Crear tablas nuevas si no existen
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 1: Crear tablas nuevas...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Todas las tablas creadas/verificadas")

        # Refrescar inspector
        inspector = inspect(engine)

        # ══════════════════════════════════════════════════════════
        # 2. Agregar columnas a POLIZAS
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 2: Agregar columnas a polizas...")

        poliza_cols = {
            "solicitud_id": "INTEGER",
            "solicitud_nosol": "VARCHAR(30)",
        }

        for col_name, col_type in poliza_cols.items():
            if not column_exists(inspector, "polizas", col_name):
                db.execute(text(f"ALTER TABLE polizas ADD COLUMN {col_name} {col_type}"))
                print(f"   ✅ polizas.{col_name} ({col_type}) agregada")
            else:
                print(f"   ⏭️  polizas.{col_name} ya existe")

        db.commit()

        # ══════════════════════════════════════════════════════════
        # 3. Agregar columnas a SOLICITUDES
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 3: Verificar tabla solicitudes...")

        if table_exists(inspector, "solicitudes"):
            sol_new_cols = {
                "nosol": "VARCHAR(30)",
                "nomramo": "VARCHAR(50)",
                "fecrecepcion": "VARCHAR(30)",
                "contratante_nombre": "VARCHAR(300)",
                "dia_recepcion": "INTEGER",
                "mes_recepcion": "INTEGER",
                "ano_recepcion": "INTEGER",
                "idagente": "VARCHAR(20)",
                "nuevo": "INTEGER",
                "antaxa": "INTEGER",
                "reingreso": "INTEGER",
                "contasol": "INTEGER",
                "numsolicitantes": "INTEGER",
                "fecha_sistema": "VARCHAR(30)",
                "subramo": "VARCHAR(50)",
                "forma_pago": "VARCHAR(30)",
                "prima_contratada": "FLOAT",
                "comision_total_sol": "FLOAT",
                "prima_pagada_sol": "FLOAT",
                "num_revires": "INTEGER",
                "f_captura_agente": "VARCHAR(30)",
                "f_envio_poliza": "VARCHAR(30)",
                "f_fin_sla": "VARCHAR(30)",
                "territorio": "VARCHAR(100)",
                "zona": "VARCHAR(100)",
                "oficina": "VARCHAR(100)",
                "canal": "VARCHAR(50)",
                "promotor_codigo": "VARCHAR(20)",
                "promotor_nombre": "VARCHAR(200)",
                "ramo_normalizado": "VARCHAR(10)",
                "dias_tramite": "INTEGER",
                "alerta_atorada": "INTEGER DEFAULT 0",
                "tasa_conversion_agente": "FLOAT",
                "sla_cumplido": "INTEGER",
                "tipo_rechazo": "VARCHAR(50)",
                "ultima_etapa": "VARCHAR(50)",
                "ultima_subetapa": "VARCHAR(50)",
                "fecha_ultima_etapa": "VARCHAR(30)",
                "observaciones_etapa": "TEXT",
                "poliza_numero": "VARCHAR(30)",
                "fuente": "VARCHAR(50) DEFAULT 'VW_CONCENTRADO'",
            }

            added = 0
            skipped = 0
            for col_name, col_type in sol_new_cols.items():
                if not column_exists(inspector, "solicitudes", col_name):
                    db.execute(text(f"ALTER TABLE solicitudes ADD COLUMN {col_name} {col_type}"))
                    added += 1
                else:
                    skipped += 1

            db.commit()
            print(f"   ✅ {added} columnas agregadas, {skipped} ya existían")
        else:
            print("   ✅ Tabla solicitudes será creada por create_all")

        # ══════════════════════════════════════════════════════════
        # 4. Agregar columna solicitud_id a ETAPAS_SOLICITUDES
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 4: Agregar FK a etapas_solicitudes...")

        if table_exists(inspector, "etapas_solicitudes"):
            if not column_exists(inspector, "etapas_solicitudes", "solicitud_id"):
                db.execute(text(
                    "ALTER TABLE etapas_solicitudes ADD COLUMN solicitud_id INTEGER"
                ))
                db.commit()
                print("   ✅ etapas_solicitudes.solicitud_id agregada")
            else:
                print("   ⏭️  etapas_solicitudes.solicitud_id ya existe")
        else:
            print("   ⏭️  Tabla etapas_solicitudes no existe aún (se creará)")

        # ══════════════════════════════════════════════════════════
        # 5. Crear índices
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 5: Crear índices...")

        indices = [
            ("ix_polizas_solicitud_nosol", "polizas", "solicitud_nosol"),
            ("ix_solicitudes_nosol", "solicitudes", "nosol"),
            ("ix_solicitudes_idagente", "solicitudes", "idagente"),
            ("ix_solicitudes_estado", "solicitudes", "estado"),
            ("ix_solicitudes_ramo_norm", "solicitudes", "ramo_normalizado"),
            ("ix_etapas_solicitud_id", "etapas_solicitudes", "solicitud_id"),
        ]

        for idx_name, tbl, col in indices:
            try:
                if table_exists(inspector, tbl) and column_exists(inspector, tbl, col):
                    db.execute(text(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl}({col})"
                    ))
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    pass
                else:
                    print(f"   ⚠️  Índice {idx_name}: {str(e)[:60]}")

        db.commit()
        print("   ✅ Índices verificados")

        # ══════════════════════════════════════════════════════════
        # 6. Reporte de estado final
        # ══════════════════════════════════════════════════════════
        inspector = inspect(engine)

        print("\n" + "=" * 60)
        print("📊 ESTADO FINAL DE LA BD")
        print("=" * 60)

        for tbl_name in ["solicitudes", "polizas", "pagos", "etapas_solicitudes",
                          "agentes", "productos", "contratantes"]:
            if table_exists(inspector, tbl_name):
                count = db.execute(text(f"SELECT COUNT(*) FROM {tbl_name}")).scalar()
                cols = len(inspector.get_columns(tbl_name))
                print(f"  {tbl_name:30s}  {count:>8,} filas  |  {cols:>3} columnas")
            else:
                print(f"  {tbl_name:30s}  (NO EXISTE)")

        elapsed = time.time() - start
        print(f"\n✅ Migración completada en {elapsed:.1f}s")
        print("   Branch: refactor/solicitud-centrico")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
