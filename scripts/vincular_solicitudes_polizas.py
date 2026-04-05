"""
Vincular Solicitudes ↔ Pólizas ↔ Etapas — Refactor v2.0
========================================================
Cruza las 3 piezas fundamentales del sistema:
1. Crea registros en tabla solicitudes a partir de etapas_solicitudes
2. Vincula solicitudes con pólizas via nosol/poliza_numero
3. Vincula etapas con solicitudes via nosol
4. Aplica reglas de negocio S1-S7

Uso:
    python scripts/vincular_solicitudes_polizas.py
"""
import os
import sys
import time
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, engine, Base
from api.rules_solicitudes import (
    normalizar_ramo,
    derivar_estado_de_etapa,
    puede_vincular_poliza,
    normalizar_poliza_para_cruce,
    detectar_solicitud_atorada,
    calcular_dias_tramite,
    evaluar_sla,
    calcular_tasa_conversion,
)


def safe_str(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s not in ("None", "nan", "") else None


def safe_int(val):
    try:
        s = str(val).strip()
        if not s or s in ("None", "nan", ""):
            return None
        return int(float(s))
    except:
        return None


def main():
    print("=" * 60)
    print("🔗 VINCULACIÓN Solicitudes ↔ Pólizas ↔ Etapas")
    print("=" * 60)
    start = time.time()

    db = SessionLocal()

    try:
        # ══════════════════════════════════════════════════════════
        # PASO 1: Crear solicitudes a partir de etapas
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 1: Crear cabeceras de solicitudes desde etapas...")

        # Obtener todas las etapas agrupadas por nosol
        etapas_raw = db.execute(text("""
            SELECT nosol, nomramo, fecrecepcion, contratante,
                   dia_recepcion, mes_recepcion, ano_recepcion,
                   etapa, subetapa, fecetapa,
                   observaciones, idagente, nuevo, antaxa, reingreso,
                   contasol, poliza, numsolicitantes, fecha_sistema,
                   dias_tramite
            FROM etapas_solicitudes
            ORDER BY nosol, fecetapa
        """)).fetchall()

        if not etapas_raw:
            print("   ⚠️  No hay etapas en la BD. Ejecuta importar_concentrado.py primero.")
            return

        print(f"   📊 {len(etapas_raw):,} registros de etapas encontrados")

        # Agrupar por nosol — tomar la ÚLTIMA etapa como cabecera
        grupos = defaultdict(list)
        for row in etapas_raw:
            grupos[row[0]].append(row)

        print(f"   📊 {len(grupos):,} solicitudes únicas detectadas")

        # Verificar solicitudes existentes
        existing = db.execute(text("SELECT nosol FROM solicitudes WHERE nosol IS NOT NULL")).fetchall()
        existing_nosol = {r[0] for r in existing if r[0]}
        print(f"   📊 {len(existing_nosol):,} solicitudes ya existen en BD")

        # Insertar solicitudes nuevas
        batch = []
        updated_count = 0

        for nosol, etapas_list in grupos.items():
            if not nosol:
                continue

            # Última etapa (la más reciente)
            ultima = etapas_list[-1]
            # Primera etapa (para datos de recepción)
            primera = etapas_list[0]

            nomramo = safe_str(primera[1])
            ramo_norm = normalizar_ramo(nomramo)
            ultima_etapa = safe_str(ultima[7])
            poliza_num = safe_str(ultima[16])

            # Aplicar reglas
            estado_result = derivar_estado_de_etapa(ultima_etapa, poliza_num)
            dias = calcular_dias_tramite(
                safe_str(primera[2]),  # fecrecepcion
                safe_str(ultima[9])   # fecetapa
            )
            alerta = detectar_solicitud_atorada(safe_str(ultima[9]), estado_result["estado"])
            sla = evaluar_sla(dias)

            record = {
                "nosol": nosol,
                "folio": nosol,  # compat legacy
                "nomramo": nomramo,
                "fecrecepcion": safe_str(primera[2]),
                "contratante_nombre": safe_str(primera[3]),
                "dia_recepcion": safe_int(primera[4]),
                "mes_recepcion": safe_int(primera[5]),
                "ano_recepcion": safe_int(primera[6]),
                "idagente": safe_str(primera[11]),
                "nuevo": safe_int(primera[12]),
                "antaxa": safe_int(primera[13]),
                "reingreso": safe_int(primera[14]),
                "contasol": safe_int(primera[15]),
                "numsolicitantes": safe_int(primera[17]) or 1,
                "fecha_sistema": safe_str(primera[18]),
                # Calculados
                "ramo_normalizado": ramo_norm,
                "estado": estado_result["estado"],
                "tipo_rechazo": estado_result["tipo_rechazo"],
                "dias_tramite": dias,
                "alerta_atorada": alerta,
                "sla_cumplido": sla,
                # Última etapa desnormalizada
                "ultima_etapa": ultima_etapa,
                "ultima_subetapa": safe_str(ultima[8]),
                "fecha_ultima_etapa": safe_str(ultima[9]),
                "observaciones_etapa": safe_str(ultima[10]),
                # Póliza
                "poliza_numero": poliza_num if puede_vincular_poliza(poliza_num) else None,
                "fuente": "VW_CONCENTRADO",
            }

            if nosol in existing_nosol:
                # UPDATE existente
                set_clause = ", ".join(f"{k} = :{k}" for k in record.keys() if k != "nosol")
                db.execute(text(
                    f"UPDATE solicitudes SET {set_clause} WHERE nosol = :nosol"
                ), record)
                updated_count += 1
            else:
                batch.append(record)

        # Batch INSERT
        if batch:
            # Construir INSERT dinámico
            cols = list(batch[0].keys())
            placeholders = ", ".join(f":{c}" for c in cols)
            col_names = ", ".join(cols)

            BATCH_SIZE = 500
            for i in range(0, len(batch), BATCH_SIZE):
                chunk = batch[i:i + BATCH_SIZE]
                db.execute(text(f"INSERT INTO solicitudes ({col_names}) VALUES ({placeholders})"), chunk)
                db.flush()

        db.commit()
        print(f"   ✅ {len(batch):,} solicitudes nuevas creadas, {updated_count:,} actualizadas")

        # ══════════════════════════════════════════════════════════
        # PASO 2: Vincular etapas → solicitudes (FK solicitud_id)
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 2: Vincular etapas con solicitudes...")

        linked_etapas = db.execute(text("""
            UPDATE etapas_solicitudes
            SET solicitud_id = (
                SELECT s.id FROM solicitudes s
                WHERE s.nosol = etapas_solicitudes.nosol
                LIMIT 1
            )
            WHERE solicitud_id IS NULL
            AND nosol IS NOT NULL
        """)).rowcount
        db.commit()
        print(f"   ✅ {linked_etapas:,} etapas vinculadas a solicitudes")

        # ══════════════════════════════════════════════════════════
        # PASO 3: Vincular solicitudes → pólizas
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 3: Vincular solicitudes con pólizas...")

        # Obtener solicitudes con póliza_numero válido
        sols_con_poliza = db.execute(text("""
            SELECT id, poliza_numero FROM solicitudes
            WHERE poliza_numero IS NOT NULL
            AND poliza_numero != ''
            AND poliza_numero != 'PENDIENTE'
        """)).fetchall()

        print(f"   📊 {len(sols_con_poliza):,} solicitudes con póliza para vincular")

        vinculadas_s2p = 0
        vinculadas_p2s = 0

        for sol_id, pol_num in sols_con_poliza:
            if not pol_num:
                continue

            pol_norm = normalizar_poliza_para_cruce(pol_num)

            # Buscar póliza por poliza_estandar o poliza_original
            poliza_row = db.execute(text("""
                SELECT id FROM polizas
                WHERE poliza_estandar = :pol_norm
                   OR poliza_original = :pol_num
                LIMIT 1
            """), {"pol_norm": pol_norm, "pol_num": pol_num}).fetchone()

            if poliza_row:
                poliza_id = poliza_row[0]

                # Actualizar póliza → solicitud
                db.execute(text("""
                    UPDATE polizas
                    SET solicitud_id = :sol_id, solicitud_nosol = :nosol
                    WHERE id = :pol_id AND solicitud_id IS NULL
                """), {"sol_id": sol_id, "nosol": pol_num, "pol_id": poliza_id})
                vinculadas_p2s += 1

                vinculadas_s2p += 1

        # También vincular al revés: pólizas que tienen campo 'solicitud' con un nosol
        rev_linked = db.execute(text("""
            UPDATE polizas
            SET solicitud_nosol = solicitud
            WHERE solicitud IS NOT NULL
            AND solicitud != ''
            AND solicitud_nosol IS NULL
        """)).rowcount

        db.commit()
        print(f"   ✅ {vinculadas_s2p:,} solicitudes vinculadas a pólizas")
        print(f"   ✅ {vinculadas_p2s:,} pólizas actualizadas con solicitud_id")
        print(f"   ✅ {rev_linked:,} pólizas con solicitud_nosol desde campo legacy")

        # ══════════════════════════════════════════════════════════
        # PASO 4: Resolver agente_id en solicitudes
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 4: Resolver agente_id en solicitudes...")

        resolved_agents = db.execute(text("""
            UPDATE solicitudes
            SET agente_id = (
                SELECT a.id FROM agentes a
                WHERE a.codigo_agente = solicitudes.idagente
                LIMIT 1
            )
            WHERE agente_id IS NULL
            AND idagente IS NOT NULL
        """)).rowcount
        db.commit()
        print(f"   ✅ {resolved_agents:,} solicitudes con agente_id resuelto")

        # ══════════════════════════════════════════════════════════
        # PASO 5: Calcular tasa de conversión por agente
        # ══════════════════════════════════════════════════════════
        print("\n📋 Paso 5: Calcular tasa de conversión por agente...")

        agente_stats = db.execute(text("""
            SELECT idagente,
                   COUNT(*) as total,
                   SUM(CASE WHEN estado IN ('EMITIDA', 'PAGADA') THEN 1 ELSE 0 END) as emitidas
            FROM solicitudes
            WHERE idagente IS NOT NULL
            GROUP BY idagente
        """)).fetchall()

        for ag_code, total, emitidas in agente_stats:
            tasa = calcular_tasa_conversion(total, emitidas)
            db.execute(text(
                "UPDATE solicitudes SET tasa_conversion_agente = :tasa WHERE idagente = :ag"
            ), {"tasa": tasa, "ag": ag_code})

        db.commit()
        print(f"   ✅ Tasa de conversión calculada para {len(agente_stats):,} agentes")

        # ══════════════════════════════════════════════════════════
        # REPORTE FINAL
        # ══════════════════════════════════════════════════════════
        elapsed = time.time() - start

        total_sol = db.execute(text("SELECT COUNT(*) FROM solicitudes")).scalar()
        sol_con_pol = db.execute(text(
            "SELECT COUNT(*) FROM solicitudes WHERE poliza_numero IS NOT NULL"
        )).scalar()
        pol_con_sol = db.execute(text(
            "SELECT COUNT(*) FROM polizas WHERE solicitud_id IS NOT NULL"
        )).scalar()
        total_pol = db.execute(text("SELECT COUNT(*) FROM polizas")).scalar()
        etapas_con_sol = db.execute(text(
            "SELECT COUNT(*) FROM etapas_solicitudes WHERE solicitud_id IS NOT NULL"
        )).scalar()
        total_etapas = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar()

        # Estado por distribución
        estados = db.execute(text("""
            SELECT estado, COUNT(*) c FROM solicitudes
            GROUP BY estado ORDER BY c DESC
        """)).fetchall()

        ramos = db.execute(text("""
            SELECT ramo_normalizado, COUNT(*) c FROM solicitudes
            WHERE ramo_normalizado IS NOT NULL
            GROUP BY ramo_normalizado ORDER BY c DESC
        """)).fetchall()

        print(f"\n{'=' * 60}")
        print(f"📊 REPORTE DE VINCULACIÓN")
        print(f"{'=' * 60}")
        print(f"  Solicitudes totales:        {total_sol:>8,}")
        print(f"  Solicitudes con póliza:     {sol_con_pol:>8,}  ({sol_con_pol/max(total_sol,1)*100:.1f}%)")
        print(f"  Pólizas con solicitud:      {pol_con_sol:>8,}  ({pol_con_sol/max(total_pol,1)*100:.1f}%)")
        print(f"  Etapas vinculadas:          {etapas_con_sol:>8,}  ({etapas_con_sol/max(total_etapas,1)*100:.1f}%)")

        print(f"\n📌 Distribución por estado:")
        for est in estados:
            print(f"    {(est[0] or 'SIN ESTADO'):20s}  {est[1]:>6,}")

        print(f"\n🏷️  Por ramo:")
        for r in ramos:
            print(f"    {(r[0] or 'SIN RAMO'):10s}  {r[1]:>6,}")

        print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
        print(f"✅ Vinculación completada!")

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
