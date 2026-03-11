"""
Importar PAGTOTAL CSV directamente a la base de datos.
Optimizado para archivos grandes (270K+ registros).

Uso:
    python scripts/importar_pagtotal.py fuentes/PAGTOTAL_202603101502.csv
"""
import os
import sys
import csv
import time
from datetime import datetime

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, engine, Base, Pago


def parse_dt(v):
    """Parsea fecha flexible: YYYY-MM-DD HH:MM:SS.sss o DD/MM/YYYY"""
    if not v or str(v).strip() in ("", "nan", "None"):
        return None
    s = str(v).strip()
    # Formato PAGTOTAL: 2023-01-19 00:00:00.000
    if " " in s:
        s = s.split(" ")[0]  # Tomar solo la fecha
    if len(s) >= 10:
        return s[:10]
    return None


def to_float(v):
    """Convierte a float, retorna 0 si falla."""
    try:
        s = str(v).replace(",", "").strip() if v else ""
        if not s or s in ("", "nan", "None"):
            return 0.0
        return float(s)
    except:
        return 0.0


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/importar_pagtotal.py <ruta_csv>")
        print("Ejemplo: python scripts/importar_pagtotal.py fuentes/PAGTOTAL_202603101502.csv")
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

    db = SessionLocal()
    start = time.time()

    try:
        # ── Paso 1: Contar registros actuales ──
        count_antes = db.execute(text("SELECT COUNT(*) FROM pagos")).scalar() or 0
        print(f"\n🗑️  Limpiando tabla pagos ({count_antes} registros anteriores)...")
        db.execute(text("DELETE FROM pagos"))
        db.commit()
        print("   ✅ Tabla pagos limpiada")

        # ── Paso 2: Leer CSV e insertar en batches ──
        print(f"\n📥 Importando pagos desde CSV...")

        # Detectar encoding
        contenido = None
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(csv_path, "r", encoding=enc) as f:
                    f.read(1000)
                contenido = enc
                break
            except:
                continue

        if not contenido:
            print("❌ No se pudo detectar el encoding del archivo")
            sys.exit(1)

        print(f"   Encoding detectado: {contenido}")

        batch = []
        total = 0
        errores = 0
        BATCH_SIZE = 10_000

        with open(csv_path, "r", encoding=contenido) as f:
            reader = csv.DictReader(f)

            # Limpiar headers
            if reader.fieldnames:
                reader.fieldnames = [h.strip().upper().replace('"', '') for h in reader.fieldnames]
                print(f"   Columnas: {', '.join(reader.fieldnames)}")

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

                    # Batch insert
                    if len(batch) >= BATCH_SIZE:
                        db.execute(text("""
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
                        """), batch)
                        db.flush()
                        elapsed = time.time() - start
                        rate = total / elapsed if elapsed > 0 else 0
                        print(f"   ⏳ {total:,} registros ({rate:.0f}/s)...", end="\r")
                        batch = []

                except Exception as e:
                    errores += 1
                    if errores <= 5:
                        print(f"   ⚠️  Error fila {i+2}: {str(e)[:80]}")

        # Insertar los restantes
        if batch:
            db.execute(text("""
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
            """), batch)

        db.commit()
        t1 = time.time() - start
        print(f"\n   ✅ {total:,} pagos importados en {t1:.1f}s ({errores} errores)")

        # ── Paso 3: Actualizar prima_acumulada_basica en pólizas ──
        print(f"\n🔗 Actualizando prima_acumulada_basica en pólizas...")

        # Verificar si estamos en SQLite o PostgreSQL
        db_url = str(engine.url)
        if "sqlite" in db_url:
            # SQLite no soporta UPDATE FROM, usar subquery
            updated = db.execute(text("""
                UPDATE polizas SET 
                    prima_acumulada_basica = (
                        SELECT SUM(p.prima_neta) 
                        FROM pagos p 
                        WHERE p.poliza_match = polizas.poliza_original
                    ),
                    updated_at = datetime('now')
                WHERE poliza_original IN (SELECT DISTINCT poliza_match FROM pagos)
            """)).rowcount
        else:
            # PostgreSQL soporta UPDATE FROM
            updated = db.execute(text("""
                UPDATE polizas SET prima_acumulada_basica = sub.total_pagado
                FROM (
                    SELECT poliza_match, SUM(prima_neta) as total_pagado
                    FROM pagos
                    GROUP BY poliza_match
                ) sub
                WHERE polizas.poliza_original = sub.poliza_match
            """)).rowcount

        db.commit()
        print(f"   ✅ {updated:,} pólizas actualizadas con prima acumulada")

        # ── Paso 4: Estadísticas finales ──
        total_final = db.execute(text("SELECT COUNT(*) FROM pagos")).scalar() or 0
        suma_primas = db.execute(text("SELECT SUM(prima_neta) FROM pagos")).scalar() or 0
        suma_comisiones = db.execute(text("SELECT SUM(comision_total) FROM pagos")).scalar() or 0
        polizas_unicas = db.execute(text("SELECT COUNT(DISTINCT poliza_match) FROM pagos")).scalar() or 0

        # Estadísticas por año
        anios = db.execute(text("""
            SELECT anio_aplicacion, COUNT(*) as cnt, SUM(prima_neta) as prima
            FROM pagos 
            WHERE anio_aplicacion IS NOT NULL
            GROUP BY anio_aplicacion 
            ORDER BY anio_aplicacion
        """)).fetchall()

        # Estadísticas por ramo
        ramos = db.execute(text("""
            SELECT ramo, COUNT(*) as cnt, SUM(prima_neta) as prima
            FROM pagos 
            WHERE ramo IS NOT NULL
            GROUP BY ramo 
            ORDER BY prima DESC
            LIMIT 10
        """)).fetchall()

        elapsed_total = time.time() - start

        print(f"\n{'='*60}")
        print(f"📊 RESUMEN DE IMPORTACIÓN PAGTOTAL")
        print(f"{'='*60}")
        print(f"  Total pagos:          {total_final:>12,}")
        print(f"  Pólizas únicas:       {polizas_unicas:>12,}")
        print(f"  Prima neta total:     ${suma_primas:>14,.2f}")
        print(f"  Comisión total:       ${suma_comisiones:>14,.2f}")
        print(f"  Pólizas actualizadas: {updated:>12,}")
        print(f"  Errores:              {errores:>12,}")
        print(f"  Tiempo total:         {elapsed_total:>12.1f}s")

        print(f"\n📅 Distribución por año:")
        for a in anios:
            print(f"    {a[0]}: {a[1]:>8,} pagos  |  ${a[2]:>14,.2f}")

        print(f"\n🏷️  Top ramos:")
        for r in ramos:
            print(f"    {r[0][:35]:35s} {r[1]:>7,} pagos  |  ${r[2]:>14,.2f}")

        print(f"\n✅ Importación completada exitosamente!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
