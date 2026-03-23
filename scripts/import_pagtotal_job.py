"""
Importa PAGTOTAL desde GCS a Cloud SQL.
Diseñado para correr como Cloud Run Job.

Variables de entorno requeridas:
  - DATABASE_URL: URL de Cloud SQL
  - GCS_BUCKET: Bucket con el CSV 
  - GCS_BLOB: Nombre del archivo en el bucket
"""
import os
import sys
import csv
import time
import tempfile

# Asegurar output inmediato a Cloud Logging
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

# Intentar importar google.cloud.storage
try:
    from google.cloud import storage as gcs_storage
except ImportError:
    print("Instalando google-cloud-storage...")
    os.system("pip install google-cloud-storage")
    from google.cloud import storage as gcs_storage

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "mag-sistema-imports-922967")
GCS_BLOB = os.environ.get("GCS_BLOB", "PAGTOTAL_202603101502.csv")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)

print(f"DB: {DATABASE_URL.split('@')[0]}@...")
print(f"GCS: gs://{GCS_BUCKET}/{GCS_BLOB}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
Session = sessionmaker(bind=engine)


def parse_dt(v):
    if not v or str(v).strip() in ("", "nan", "None"):
        return None
    s = str(v).strip()
    if " " in s:
        s = s.split(" ")[0]
    return s[:10] if len(s) >= 10 else None


def to_float(v):
    try:
        s = str(v).replace(",", "").strip() if v else ""
        if not s or s in ("", "nan", "None"):
            return 0.0
        return float(s)
    except:
        return 0.0


def main():
    start = time.time()
    db = Session()

    try:
        # 1. Descargar CSV de GCS
        print("\n[1/4] Descargando CSV de GCS...")
        client = gcs_storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(GCS_BLOB)
        
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        blob.download_to_file(tmp)
        tmp.close()
        file_size = os.path.getsize(tmp.name) / (1024 * 1024)
        print(f"  ✅ Descargado: {file_size:.1f} MB -> {tmp.name}")

        # 2. Limpiar tabla pagos
        print("\n[2/4] Limpiando tabla pagos...")
        count_antes = db.execute(text("SELECT COUNT(*) FROM pagos")).scalar() or 0
        db.execute(text("TRUNCATE TABLE pagos"))
        db.commit()
        print(f"  ✅ {count_antes} registros eliminados (TRUNCATE)", flush=True)

        # 3. Importar CSV
        print("\n[3/4] Importando pagos...")
        
        # Detectar encoding
        detected_enc = "utf-8"
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(tmp.name, "r", encoding=enc) as f:
                    f.read(2000)
                detected_enc = enc
                break
            except:
                continue
        print(f"  Encoding: {detected_enc}")

        INSERT_SQL = text("""
            INSERT INTO pagos (
                poliza_numero, endoso, agente_codigo, contratante, ramo, moneda,
                fecha_inicio, fecha_aplicacion, comprobante,
                prima_neta, prima_total, comision, comision_derecho, comision_recargo,
                comision_total, promotor, poliza_match,
                anio_aplicacion, periodo_aplicacion, fuente
            ) VALUES (
                :poliza_numero, :endoso, :agente_codigo, :contratante, :ramo, :moneda,
                :fecha_inicio, :fecha_aplicacion, :comprobante,
                :prima_neta, :prima_total, :comision, :comision_derecho, :comision_recargo,
                :comision_total, :promotor, :poliza_match,
                :anio_aplicacion, :periodo_aplicacion, :fuente
            )
        """)

        batch = []
        total = 0
        errores = 0
        BATCH_SIZE = 2000

        with open(tmp.name, "r", encoding=detected_enc) as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                reader.fieldnames = [h.strip().upper().replace('"', '') for h in reader.fieldnames]
                print(f"  Columnas: {', '.join(reader.fieldnames[:5])}...")

            for i, row in enumerate(reader):
                try:
                    poliza = (row.get("POLIZA") or "").strip().replace('"', '')
                    if not poliza or poliza == "nan":
                        continue

                    fec_apli = parse_dt(row.get("FECAPLI"))
                    anio = int(fec_apli[:4]) if fec_apli and len(fec_apli) >= 4 else None
                    periodo = fec_apli[:7] if fec_apli and len(fec_apli) >= 7 else None

                    batch.append({
                        "poliza_numero": poliza,
                        "endoso": (row.get("ENDOSO") or "").strip().replace('"', '') or None,
                        "agente_codigo": (row.get("AGENTE") or "").strip().replace('"', '') or None,
                        "contratante": (row.get("CONTRATANTE") or "").strip().replace('"', '') or None,
                        "ramo": (row.get("RAMO") or "").strip().replace('"', '') or None,
                        "moneda": (row.get("MON") or "MN").strip().replace('"', ''),
                        "fecha_inicio": parse_dt(row.get("PERINI")),
                        "fecha_aplicacion": fec_apli,
                        "comprobante": (row.get("COMPROBANTE") or "").strip().replace('"', '') or None,
                        "prima_neta": to_float(row.get("NETA")),
                        "prima_total": to_float(row.get("PRITOT")),
                        "comision": to_float(row.get("COMISION")),
                        "comision_derecho": to_float(row.get("COMDERECHO")),
                        "comision_recargo": to_float(row.get("COMRECARGO")),
                        "comision_total": to_float(row.get("TOTCOMISION")),
                        "promotor": (row.get("PROMOTOR") or "").strip().replace('"', '') or None,
                        "poliza_match": (row.get("POLIZA_MATCH") or poliza).strip().replace('"', ''),
                        "anio_aplicacion": anio,
                        "periodo_aplicacion": periodo,
                        "fuente": "PAGTOTAL",
                    })
                    total += 1

                    if len(batch) >= BATCH_SIZE:
                        db.execute(INSERT_SQL, batch)
                        db.commit()
                        elapsed = time.time() - start
                        rate = total / elapsed if elapsed > 0 else 0
                        print(f"  {total:>8,} registros ({rate:.0f}/s)...", flush=True)
                        batch = []

                except Exception as e:
                    errores += 1
                    if errores <= 5:
                        print(f"  ⚠️ Error fila {i+2}: {str(e)[:80]}")

        if batch:
            db.execute(INSERT_SQL, batch)
            db.commit()

        t1 = time.time() - start
        print(f"  ✅ {total:,} pagos importados en {t1:.1f}s ({errores} errores)")

        # Limpiar temp
        os.unlink(tmp.name)

        # 4. Actualizar polizas + contratantes
        print("\n[4/4] Post-procesamiento...")

        # Prima acumulada
        updated = db.execute(text("""
            UPDATE polizas SET prima_acumulada_basica = sub.total_pagado
            FROM (
                SELECT poliza_match, SUM(prima_neta) as total_pagado
                FROM pagos GROUP BY poliza_match
            ) sub
            WHERE polizas.poliza_original = sub.poliza_match
        """)).rowcount
        db.commit()
        print(f"  ✅ {updated:,} pólizas actualizadas con prima acumulada")

        # Contratantes
        contratantes_nuevos = db.execute(text("""
            INSERT INTO contratantes (nombre, created_at, updated_at)
            SELECT DISTINCT contratante, NOW()::TEXT, NOW()::TEXT
            FROM pagos
            WHERE contratante IS NOT NULL AND contratante != ''
            AND contratante NOT IN (SELECT nombre FROM contratantes)
        """)).rowcount
        db.commit()
        print(f"  ✅ {contratantes_nuevos:,} contratantes nuevos")

        # Stats finales
        total_pagos = db.execute(text("SELECT COUNT(*) FROM pagos")).scalar()
        suma_prima = db.execute(text("SELECT COALESCE(SUM(prima_neta),0) FROM pagos")).scalar()
        suma_comision = db.execute(text("SELECT COALESCE(SUM(comision_total),0) FROM pagos")).scalar()
        total_contratantes = db.execute(text("SELECT COUNT(*) FROM contratantes")).scalar()
        elapsed = time.time() - start

        print(f"\n{'='*60}")
        print(f"  IMPORTACIÓN PAGTOTAL COMPLETADA")
        print(f"{'='*60}")
        print(f"  Pagos:         {total_pagos:>10,}")
        print(f"  Prima total:   ${suma_prima:>14,.2f}")
        print(f"  Comisión:      ${suma_comision:>14,.2f}")
        print(f"  Pólizas upd:   {updated:>10,}")
        print(f"  Contratantes:  {total_contratantes:>10,}")
        print(f"  Errores:       {errores:>10,}")
        print(f"  Tiempo:        {elapsed:>10.1f}s")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
