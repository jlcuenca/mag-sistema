"""
╔══════════════════════════════════════════════════════════════════╗
║  FASE 5 — Auditoría y Recálculo Batch de Solicitudes           ║
║  MAG Sistema · Refactorización Solicitud-Céntrica              ║
╚══════════════════════════════════════════════════════════════════╝

Script que:
  1. Audita la integridad de datos de la cadena Solicitud→Póliza→Pagos
  2. Recalcula reglas S1-S7 sobre TODAS las solicitudes
  3. Actualiza la última etapa desnormalizada en cada solicitud
  4. Calcula tasa de conversión por agente (S5)
  5. Genera reporte final con métricas

Uso: python scripts/fase5_auditoria.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from collections import Counter, defaultdict
from sqlalchemy import text
from api.database import SessionLocal, engine
from api.rules_solicitudes import (
    normalizar_ramo, derivar_estado_de_etapa, detectar_solicitud_atorada,
    calcular_dias_tramite, evaluar_sla, calcular_tasa_conversion, puede_vincular_poliza,
    normalizar_poliza_para_cruce,
)


def banner(msg):
    print(f"\n{'═'*60}")
    print(f"  {msg}")
    print(f"{'═'*60}")


def main():
    start = datetime.now()
    banner("FASE 5 — Auditoría y Recálculo Batch")
    print(f"  Inicio: {start.strftime('%Y-%m-%d %H:%M:%S')}")

    db = SessionLocal()
    try:
        # ──────────────────────────────────────────────────────────
        # PASO 1: Datos crudos
        # ──────────────────────────────────────────────────────────
        banner("PASO 1: Inventario de datos")

        total_sol = db.execute(text("SELECT COUNT(*) FROM solicitudes")).scalar()
        total_pol = db.execute(text("SELECT COUNT(*) FROM polizas")).scalar()
        total_pag = db.execute(text("SELECT COUNT(*) FROM pagos")).scalar()
        total_eta = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes")).scalar()

        print(f"  Solicitudes:  {total_sol:,}")
        print(f"  Pólizas:      {total_pol:,}")
        print(f"  Pagos:        {total_pag:,}")
        print(f"  Etapas:       {total_eta:,}")

        # ──────────────────────────────────────────────────────────
        # PASO 2: Desnormalizar última etapa en cada solicitud
        # ──────────────────────────────────────────────────────────
        banner("PASO 2: Desnormalizar última etapa por solicitud")

        # Get latest etapa per nosol
        etapas_raw = db.execute(text("""
            SELECT e.nosol, e.etapa, e.subetapa, e.fecetapa, e.observaciones, e.dias_tramite
            FROM etapas_solicitudes e
            INNER JOIN (
                SELECT nosol, MAX(fecetapa) as max_fecha
                FROM etapas_solicitudes
                GROUP BY nosol
            ) latest ON e.nosol = latest.nosol AND e.fecetapa = latest.max_fecha
        """)).mappings().all()

        etapa_map = {}
        for e in etapas_raw:
            nosol = e["nosol"]
            if nosol:
                etapa_map[nosol] = dict(e)

        updated_etapa = 0
        for nosol, e in etapa_map.items():
            db.execute(text("""
                UPDATE solicitudes SET
                    ultima_etapa = :etapa,
                    ultima_subetapa = :subetapa,
                    fecha_ultima_etapa = :fecetapa,
                    observaciones_etapa = :obs
                WHERE nosol = :nosol
            """), {
                "etapa": e.get("etapa"),
                "subetapa": e.get("subetapa"),
                "fecetapa": e.get("fecetapa"),
                "obs": e.get("observaciones"),
                "nosol": nosol,
            })
            updated_etapa += 1

        db.commit()
        print(f"  ✅ {updated_etapa:,} solicitudes actualizadas con última etapa")

        # ──────────────────────────────────────────────────────────
        # PASO 3: Recalcular reglas S1-S4, S6-S7
        # ──────────────────────────────────────────────────────────
        banner("PASO 3: Recálculo batch de reglas S1-S7")

        sols_raw = db.execute(text("""
            SELECT id, nosol, nomramo, ramo, ultima_etapa, poliza_numero,
                   fecrecepcion, fecha_ultima_etapa, estado, idagente
            FROM solicitudes
        """)).mappings().all()

        batch_updates = []
        counters = Counter()

        for sol in sols_raw:
            s = dict(sol)

            # S1: Normalizar ramo
            ramo_norm = normalizar_ramo(s.get("nomramo") or s.get("ramo") or "")

            # S2: Estado de etapa
            etapa = s.get("ultima_etapa") or ""
            poliza = s.get("poliza_numero") or ""
            estado_result = derivar_estado_de_etapa(etapa, poliza)

            # S6: Días trámite
            dias = calcular_dias_tramite(
                s.get("fecrecepcion") or "",
                s.get("fecha_ultima_etapa") or ""
            )

            # S4: Alerta atorada
            alerta = detectar_solicitud_atorada(
                s.get("fecha_ultima_etapa"),
                estado_result["estado"]
            )

            # S7: SLA
            sla = evaluar_sla(dias)

            counters[estado_result["estado"]] += 1
            if alerta == 1:
                counters["ATORADAS"] += 1

            batch_updates.append({
                "id": s["id"],
                "ramo_normalizado": ramo_norm,
                "estado": estado_result["estado"],
                "tipo_rechazo": estado_result.get("tipo_rechazo"),
                "dias_tramite": dias,
                "alerta_atorada": alerta,
                "sla_cumplido": sla,
            })

        # Batch UPDATE in chunks of 500
        for i in range(0, len(batch_updates), 500):
            chunk = batch_updates[i:i+500]
            for u in chunk:
                db.execute(text("""
                    UPDATE solicitudes SET
                        ramo_normalizado = :ramo_normalizado,
                        estado = :estado,
                        tipo_rechazo = :tipo_rechazo,
                        dias_tramite = :dias_tramite,
                        alerta_atorada = :alerta_atorada,
                        sla_cumplido = :sla_cumplido,
                        updated_at = :now
                    WHERE id = :id
                """), {**u, "now": datetime.now().isoformat()})
            db.commit()
            print(f"  ... procesados {min(i+500, len(batch_updates)):,} / {len(batch_updates):,}")

        print(f"\n  Distribución de estados:")
        for estado, cnt in sorted(counters.items(), key=lambda x: -x[1]):
            print(f"    {estado:15s} → {cnt:,}")

        # ──────────────────────────────────────────────────────────
        # PASO 4: Tasa de conversión por agente (S5)
        # ──────────────────────────────────────────────────────────
        banner("PASO 4: Tasa de conversión por agente (S5)")

        agentes_stats = db.execute(text("""
            SELECT idagente,
                   COUNT(*) as total,
                   SUM(CASE WHEN estado IN ('EMITIDA','PAGADA') THEN 1 ELSE 0 END) as emitidas
            FROM solicitudes
            WHERE idagente IS NOT NULL AND idagente != ''
            GROUP BY idagente
        """)).mappings().all()

        updated_agentes = 0
        for a in agentes_stats:
            tasa = calcular_tasa_conversion(a["total"], a["emitidas"])
            db.execute(text("""
                UPDATE solicitudes SET tasa_conversion_agente = :tasa
                WHERE idagente = :idagente
            """), {"tasa": tasa, "idagente": a["idagente"]})
            updated_agentes += 1

        db.commit()
        print(f"  ✅ {updated_agentes:,} agentes con tasa actualizada")

        # ──────────────────────────────────────────────────────────
        # PASO 5: Auditoría de vinculación Solicitud→Póliza
        # ──────────────────────────────────────────────────────────
        banner("PASO 5: Auditoría Solicitud → Póliza")

        sol_con_poliza = db.execute(text("""
            SELECT COUNT(*) FROM solicitudes
            WHERE poliza_numero IS NOT NULL AND poliza_numero != ''
        """)).scalar()

        sol_sin_poliza = total_sol - sol_con_poliza

        # Verificar cuántas polizas de solicitudes se encuentran en tabla polizas
        matches = db.execute(text("""
            SELECT COUNT(DISTINCT s.id) FROM solicitudes s
            INNER JOIN polizas p ON (
                p.poliza_estandar = s.poliza_numero OR
                p.poliza_original = s.poliza_numero
            )
            WHERE s.poliza_numero IS NOT NULL AND s.poliza_numero != ''
        """)).scalar()

        print(f"  Solicitudes con póliza asignada:   {sol_con_poliza:,} ({sol_con_poliza/total_sol*100:.1f}%)")
        print(f"  Solicitudes sin póliza:            {sol_sin_poliza:,}")
        print(f"  Pólizas encontradas en tabla:      {matches:,} de {sol_con_poliza:,}")
        if sol_con_poliza > 0:
            print(f"  Tasa match póliza:                 {matches/sol_con_poliza*100:.1f}%")

        # ──────────────────────────────────────────────────────────
        # PASO 6: Auditoría Póliza→Pagos
        # ──────────────────────────────────────────────────────────
        banner("PASO 6: Auditoría Póliza → Pagos")

        pol_con_pagos = db.execute(text("""
            SELECT COUNT(DISTINCT p.id)
            FROM polizas p
            INNER JOIN pagos pg ON (
                pg.poliza_match = p.poliza_estandar OR
                pg.poliza_numero = p.poliza_original
            )
        """)).scalar()

        pagos_huerfanos = db.execute(text("""
            SELECT COUNT(pg.id)
            FROM pagos pg
            LEFT JOIN polizas p ON (
                pg.poliza_match = p.poliza_estandar OR
                pg.poliza_numero = p.poliza_original
            )
            WHERE p.id IS NULL
        """)).scalar()

        print(f"  Pólizas con al menos 1 pago:       {pol_con_pagos:,} de {total_pol:,} ({pol_con_pagos/max(total_pol,1)*100:.1f}%)")
        print(f"  Pagos huérfanos (sin póliza):       {pagos_huerfanos:,} de {total_pag:,}")

        # ──────────────────────────────────────────────────────────
        # PASO 7: Cadena completa Solicitud→Póliza→Pagos
        # ──────────────────────────────────────────────────────────
        banner("PASO 7: Cadena completa Solicitud → Póliza → Pagos")

        cadena_completa = db.execute(text("""
            SELECT COUNT(DISTINCT s.id)
            FROM solicitudes s
            INNER JOIN polizas p ON (
                p.poliza_estandar = s.poliza_numero OR
                p.poliza_original = s.poliza_numero
            )
            INNER JOIN pagos pg ON (
                pg.poliza_match = p.poliza_estandar OR
                pg.poliza_numero = p.poliza_original
            )
            WHERE s.poliza_numero IS NOT NULL AND s.poliza_numero != ''
        """)).scalar()

        print(f"  Solicitudes con cadena completa:    {cadena_completa:,}")
        print(f"  (Sol→Pol→Pago trazable de punta a punta)")

        # ──────────────────────────────────────────────────────────
        # PASO 8: Distribución por ramo normalizado
        # ──────────────────────────────────────────────────────────
        banner("PASO 8: Distribución por ramo normalizado")

        ramo_dist = db.execute(text("""
            SELECT ramo_normalizado, COUNT(*) as cnt,
                   SUM(CASE WHEN estado = 'EMITIDA' THEN 1 ELSE 0 END) as emitidas,
                   SUM(CASE WHEN estado = 'RECHAZADA' THEN 1 ELSE 0 END) as rechazadas,
                   ROUND(AVG(CASE WHEN dias_tramite IS NOT NULL THEN dias_tramite END), 1) as prom_dias
            FROM solicitudes
            GROUP BY ramo_normalizado
            ORDER BY cnt DESC
        """)).mappings().all()

        print(f"  {'Ramo':<15} {'Total':>8} {'Emit':>8} {'Rech':>8} {'Tasa':>8} {'PromDías':>10}")
        print(f"  {'─'*15} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")
        for r in ramo_dist:
            total_r = r["cnt"]
            tasa_r = (r["emitidas"]/total_r*100) if total_r > 0 else 0
            print(f"  {r['ramo_normalizado'] or 'N/A':<15} {total_r:>8,} {r['emitidas']:>8,} {r['rechazadas']:>8,} {tasa_r:>7.1f}% {r['prom_dias'] or 0:>10}")

        # ──────────────────────────────────────────────────────────
        # RESUMEN FINAL
        # ──────────────────────────────────────────────────────────
        elapsed = (datetime.now() - start).total_seconds()
        banner("RESUMEN FINAL")

        print(f"""
  📋 Solicitudes:         {total_sol:,}
  📋 Pólizas:             {total_pol:,}
  💰 Pagos:               {total_pag:,}
  ⏱️ Etapas:              {total_eta:,}

  ── Reglas recalculadas ──────────────────
  ✅ S1 Ramo normalizado:  {total_sol:,} OK
  ✅ S2 Estado derivado:   {total_sol:,} OK
  ✅ S3 Vinculación:       {sol_con_poliza:,} con póliza ({sol_con_poliza/total_sol*100:.1f}%)
  ✅ S4 Alertas atoradas:  {counters.get('ATORADAS',0):,}
  ✅ S5 Tasa conversión:   {updated_agentes:,} agentes
  ✅ S6 Días trámite:      {total_sol:,} OK
  ✅ S7 SLA evaluado:      {total_sol:,} OK

  ── Integridad de cadena ─────────────────
  Solicitud → Póliza:     {matches:,} / {sol_con_poliza:,} ({matches/max(sol_con_poliza,1)*100:.1f}%)
  Póliza → Pago:          {pol_con_pagos:,} / {total_pol:,} ({pol_con_pagos/max(total_pol,1)*100:.1f}%)
  Cadena completa:        {cadena_completa:,} trazables punta a punta
  Pagos huérfanos:        {pagos_huerfanos:,}

  ⏱️ Tiempo total: {elapsed:.1f}s
        """)

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
