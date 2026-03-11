"""
Importar VW_CONCENTRADO_ETAPAS CSV a la base de datos.
Pipeline de solicitudes AXA con tracking de etapas.

Uso:
    python scripts/importar_concentrado.py fuentes/VW_CONCENTRADO_ETAPAS_202603101509.csv
"""
import os
import sys
import csv
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, engine, Base


def parse_dt(v):
    if not v or str(v).strip() in ("", "nan", "None"):
        return None
    s = str(v).strip().replace('"', '')
    if " " in s:
        s = s.split(" ")[0]
    return s[:10] if len(s) >= 10 else None


def to_int(v):
    try:
        s = str(v).replace('"', '').strip()
        if not s or s in ("nan", "None", ""):
            return None
        return int(float(s))
    except:
        return None


def clean(v):
    if v is None:
        return None
    s = str(v).replace('"', '').strip()
    return s if s and s not in ("nan", "None") else None


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/importar_concentrado.py <ruta_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(BASE_DIR, csv_path)

    if not os.path.exists(csv_path):
        print(f"❌ Archivo no encontrado: {csv_path}")
        sys.exit(1)

    file_size = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"📂 Archivo: {csv_path}")
    print(f"📏 Tamaño: {file_size:.1f} MB")

    # Crear tabla si no existe
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    start = time.time()

    try:
        # Limpiar tabla
        count_antes = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar() or 0
        print(f"\n🗑️  Limpiando tabla etapas_solicitudes ({count_antes} registros)...")
        db.execute(text("DELETE FROM etapas_solicitudes"))
        db.commit()

        # Detectar encoding
        encoding = None
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(csv_path, "r", encoding=enc) as f:
                    f.read(2000)
                encoding = enc
                break
            except:
                continue

        print(f"   Encoding: {encoding}")

        batch = []
        total = 0
        errores = 0
        BATCH_SIZE = 5000

        with open(csv_path, "r", encoding=encoding) as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                reader.fieldnames = [h.strip().upper().replace('"', '') for h in reader.fieldnames]
                print(f"   Columnas: {', '.join(reader.fieldnames)}")

            for i, row in enumerate(reader):
                try:
                    nosol = clean(row.get("NOSOL"))
                    if not nosol:
                        continue

                    fec_recep = parse_dt(row.get("FECRECEPCION"))
                    fec_etapa = parse_dt(row.get("FECETAPA"))

                    # Calcular días de trámite
                    dias_tramite = None
                    if fec_recep and fec_etapa:
                        try:
                            d1 = datetime.strptime(fec_recep, "%Y-%m-%d")
                            d2 = datetime.strptime(fec_etapa, "%Y-%m-%d")
                            dias_tramite = (d2 - d1).days
                        except:
                            pass

                    batch.append({
                        "nosol": nosol,
                        "nomramo": clean(row.get("NOMRAMO")),
                        "fecrecepcion": fec_recep,
                        "contratante": clean(row.get("CONTRATANTE")),
                        "dia_recepcion": to_int(row.get("DIA_RECEPCION")),
                        "mes_recepcion": to_int(row.get("MES_RECEPCION")),
                        "ano_recepcion": to_int(row.get("ANO_RECEPCION")),
                        "etapa": clean(row.get("ETAPA")),
                        "subetapa": clean(row.get("SUBETAPA")),
                        "fecetapa": fec_etapa,
                        "dia_etapa": to_int(row.get("DIA_ETAPA")),
                        "mes_etapa": to_int(row.get("MES_ETAPA")),
                        "ano_etapa": to_int(row.get("ANO_ETAPA")),
                        "observaciones": clean(row.get("OBSERVACIONES")),
                        "idagente": clean(row.get("IDAGENTE")),
                        "nuevo": to_int(row.get("NUEVO")),
                        "antaxa": to_int(row.get("ANTAXA")),
                        "reingreso": to_int(row.get("REINGRESO")),
                        "contasol": to_int(row.get("CONTASOL")),
                        "poliza": clean(row.get("POLIZA")),
                        "numsolicitantes": to_int(row.get("NUMSOLICITANTES")) or 1,
                        "fecha_sistema": parse_dt(row.get("FECHA_SISTEMA")),
                        "dias_tramite": dias_tramite,
                        "fuente": "VW_CONCENTRADO",
                    })
                    total += 1

                    if len(batch) >= BATCH_SIZE:
                        db.execute(text("""
                            INSERT INTO etapas_solicitudes (
                                nosol, nomramo, fecrecepcion, contratante,
                                dia_recepcion, mes_recepcion, ano_recepcion,
                                etapa, subetapa, fecetapa,
                                dia_etapa, mes_etapa, ano_etapa,
                                observaciones, idagente, nuevo, antaxa, reingreso,
                                contasol, poliza, numsolicitantes, fecha_sistema,
                                dias_tramite, fuente
                            ) VALUES (
                                :nosol, :nomramo, :fecrecepcion, :contratante,
                                :dia_recepcion, :mes_recepcion, :ano_recepcion,
                                :etapa, :subetapa, :fecetapa,
                                :dia_etapa, :mes_etapa, :ano_etapa,
                                :observaciones, :idagente, :nuevo, :antaxa, :reingreso,
                                :contasol, :poliza, :numsolicitantes, :fecha_sistema,
                                :dias_tramite, :fuente
                            )
                        """), batch)
                        db.flush()
                        print(f"   ⏳ {total:,} registros...", end="\r")
                        batch = []

                except Exception as e:
                    errores += 1
                    if errores <= 5:
                        print(f"   ⚠️  Error fila {i+2}: {str(e)[:80]}")

        if batch:
            db.execute(text("""
                INSERT INTO etapas_solicitudes (
                    nosol, nomramo, fecrecepcion, contratante,
                    dia_recepcion, mes_recepcion, ano_recepcion,
                    etapa, subetapa, fecetapa,
                    dia_etapa, mes_etapa, ano_etapa,
                    observaciones, idagente, nuevo, antaxa, reingreso,
                    contasol, poliza, numsolicitantes, fecha_sistema,
                    dias_tramite, fuente
                ) VALUES (
                    :nosol, :nomramo, :fecrecepcion, :contratante,
                    :dia_recepcion, :mes_recepcion, :ano_recepcion,
                    :etapa, :subetapa, :fecetapa,
                    :dia_etapa, :mes_etapa, :ano_etapa,
                    :observaciones, :idagente, :nuevo, :antaxa, :reingreso,
                    :contasol, :poliza, :numsolicitantes, :fecha_sistema,
                    :dias_tramite, :fuente
                )
            """), batch)

        db.commit()
        t1 = time.time() - start
        print(f"\n   ✅ {total:,} etapas importadas en {t1:.1f}s ({errores} errores)")

        # Estadísticas
        total_db = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar()

        etapas = db.execute(text("""
            SELECT etapa, COUNT(*) c FROM etapas_solicitudes
            GROUP BY etapa ORDER BY c DESC
        """)).fetchall()

        ramos = db.execute(text("""
            SELECT nomramo, COUNT(*) c FROM etapas_solicitudes
            GROUP BY nomramo ORDER BY c DESC
        """)).fetchall()

        anios = db.execute(text("""
            SELECT ano_recepcion, COUNT(*) c FROM etapas_solicitudes
            WHERE ano_recepcion IS NOT NULL
            GROUP BY ano_recepcion ORDER BY ano_recepcion
        """)).fetchall()

        avg_dias = db.execute(text("""
            SELECT AVG(dias_tramite) FROM etapas_solicitudes
            WHERE dias_tramite IS NOT NULL AND dias_tramite >= 0
        """)).scalar()

        elapsed = time.time() - start

        print(f"\n{'='*60}")
        print(f"📊 RESUMEN CONCENTRADO ETAPAS")
        print(f"{'='*60}")
        print(f"  Total registros:      {total_db:>8,}")
        print(f"  Promedio días trámite:{avg_dias:>8.1f}" if avg_dias else "  Promedio días:        N/A")
        print(f"  Tiempo total:         {elapsed:>8.1f}s")

        print(f"\n📌 Distribución por etapa:")
        for e in etapas:
            print(f"    {e[0] or 'SIN ETAPA':30s} {e[1]:>6,}")

        print(f"\n🏷️  Por ramo:")
        for r in ramos:
            print(f"    {r[0] or 'SIN RAMO':20s} {r[1]:>6,}")

        print(f"\n📅 Por año:")
        for a in anios:
            print(f"    {a[0]}: {a[1]:>6,}")

        print(f"\n✅ Importación completada!")

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
