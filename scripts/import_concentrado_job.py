"""
Importa Concentrado (solicitudes/pipeline) desde GCS a Cloud SQL.
Diseñado para correr como Cloud Run Job.

El CSV tiene formato:
- Línea 1: "CONCENTRADO" (título, se ignora)
- Línea 2: vacía (se ignora)
- Línea 3: headers reales
- Línea 4+: datos
"""
import os
import sys
import csv
import time
import tempfile

os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

try:
    from google.cloud import storage as gcs_storage
except ImportError:
    os.system("pip install google-cloud-storage")
    from google.cloud import storage as gcs_storage

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "mag-sistema-imports-922967")
GCS_BLOB = os.environ.get("GCS_BLOB", "Concentrado2026-02-27.csv")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada")
    sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)


def parse_dt(v):
    if not v or str(v).strip() in ("", "nan", "None", "null"):
        return None
    s = str(v).strip().replace('"', '')
    if " " in s:
        s = s.split(" ")[0]
    # Handle DD/MM/YYYY
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3 and len(parts[2]) == 4:
            s = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return s[:10] if len(s) >= 10 else None


def to_int(v):
    try:
        s = str(v).replace('"', '').strip()
        if not s or s in ("nan", "None", "null", ""):
            return None
        return int(float(s))
    except:
        return None


def clean(v):
    if v is None:
        return None
    s = str(v).replace('"', '').strip()
    return s if s and s not in ("nan", "None", "null") else None


def main():
    start = time.time()
    db = Session()

    try:
        # 1. Descargar CSV
        print("[1/3] Descargando CSV de GCS...", flush=True)
        client = gcs_storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(GCS_BLOB)
        tmp = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        blob.download_to_file(tmp)
        tmp.close()
        print(f"  Descargado: {os.path.getsize(tmp.name)/1024:.1f} KB", flush=True)

        # 2. Limpiar tabla
        print("[2/3] Limpiando tabla etapas_solicitudes...", flush=True)
        count_antes = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar() or 0
        db.execute(text("TRUNCATE TABLE etapas_solicitudes"))
        db.commit()
        print(f"  {count_antes} registros eliminados", flush=True)

        # 3. Importar
        print("[3/3] Importando...", flush=True)

        # Detectar encoding
        detected_enc = "utf-8"
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                with open(tmp.name, "r", encoding=enc) as f:
                    f.read(2000)
                detected_enc = enc
                break
            except:
                continue

        # Leer archivo, saltando las primeras 2 líneas (título + vacía)
        with open(tmp.name, "r", encoding=detected_enc) as f:
            lines = f.readlines()

        # Encontrar la línea del header (contiene "NoSol")
        header_idx = 0
        for i, line in enumerate(lines):
            if "NoSol" in line or "NOSOL" in line.upper():
                header_idx = i
                break

        csv_text = "".join(lines[header_idx:])
        import io
        reader = csv.DictReader(io.StringIO(csv_text))

        if reader.fieldnames:
            reader.fieldnames = [h.strip().replace('"', '') for h in reader.fieldnames]
            print(f"  Columnas: {', '.join(reader.fieldnames[:8])}...", flush=True)

        INSERT_SQL = text("""
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
        """)

        batch = []
        total = 0
        errores = 0

        for i, row in enumerate(reader):
            try:
                nosol = clean(row.get("NoSol"))
                if not nosol:
                    continue

                fec_recep = parse_dt(row.get("F_Recepcion"))
                fec_etapa = parse_dt(row.get("Fecha_Etapa"))

                # Calcular días trámite
                dias_tramite = None
                if fec_recep and fec_etapa:
                    try:
                        d1 = datetime.strptime(fec_recep, "%Y-%m-%d")
                        d2 = datetime.strptime(fec_etapa, "%Y-%m-%d")
                        dias_tramite = (d2 - d1).days
                    except:
                        pass

                # Extraer mes/año de recepción
                mes_recep = None
                ano_recep = None
                if fec_recep:
                    try:
                        mes_recep = int(fec_recep[5:7])
                        ano_recep = int(fec_recep[:4])
                    except:
                        pass

                mes_etapa = None
                ano_etapa = None
                dia_etapa = None
                if fec_etapa:
                    try:
                        dia_etapa = int(fec_etapa[8:10])
                        mes_etapa = int(fec_etapa[5:7])
                        ano_etapa = int(fec_etapa[:4])
                    except:
                        pass

                dia_recep = None
                if fec_recep:
                    try:
                        dia_recep = int(fec_recep[8:10])
                    except:
                        pass

                batch.append({
                    "nosol": nosol,
                    "nomramo": clean(row.get("Ramo")),
                    "fecrecepcion": fec_recep,
                    "contratante": clean(row.get("Contratante")),
                    "dia_recepcion": dia_recep,
                    "mes_recepcion": mes_recep,
                    "ano_recepcion": ano_recep,
                    "etapa": clean(row.get("Etapa")),
                    "subetapa": clean(row.get("SubEtapa")),
                    "fecetapa": fec_etapa,
                    "dia_etapa": dia_etapa,
                    "mes_etapa": mes_etapa,
                    "ano_etapa": ano_etapa,
                    "observaciones": clean(row.get("Observaciones_Ag")),
                    "idagente": clean(row.get("Id_Agente_Registro")),
                    "nuevo": 1 if clean(row.get("Tipo_Tramite")) == "NUEVA" else 0,
                    "antaxa": 0,
                    "reingreso": 0,
                    "contasol": to_int(row.get("No_Solicitantes")),
                    "poliza": clean(row.get("No_Poliza")),
                    "numsolicitantes": to_int(row.get("No_Solicitantes")) or 1,
                    "fecha_sistema": parse_dt(row.get("F_Captura_Ag")),
                    "dias_tramite": dias_tramite,
                    "fuente": "CONCENTRADO",
                })
                total += 1

            except Exception as e:
                errores += 1
                if errores <= 5:
                    print(f"  Error fila {i+2}: {str(e)[:80]}", flush=True)

        if batch:
            db.execute(INSERT_SQL, batch)
        db.commit()

        os.unlink(tmp.name)

        # Stats
        total_db = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar()
        etapas = db.execute(text("""
            SELECT etapa, COUNT(*) c FROM etapas_solicitudes
            GROUP BY etapa ORDER BY c DESC
        """)).fetchall()
        ramos = db.execute(text("""
            SELECT nomramo, COUNT(*) c FROM etapas_solicitudes
            GROUP BY nomramo ORDER BY c DESC
        """)).fetchall()

        elapsed = time.time() - start
        print(f"\n{'='*50}", flush=True)
        print(f"  IMPORTACION CONCENTRADO COMPLETADA", flush=True)
        print(f"{'='*50}", flush=True)
        print(f"  Total: {total_db} registros", flush=True)
        print(f"  Errores: {errores}", flush=True)
        print(f"  Tiempo: {elapsed:.1f}s", flush=True)
        print(f"\n  Etapas:", flush=True)
        for e in etapas:
            print(f"    {e[0] or 'SIN ETAPA':30s} {e[1]:>4}", flush=True)
        print(f"\n  Ramos:", flush=True)
        for r in ramos:
            print(f"    {r[0] or 'SIN RAMO':20s} {r[1]:>4}", flush=True)

    except Exception as e:
        db.rollback()
        print(f"ERROR: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
