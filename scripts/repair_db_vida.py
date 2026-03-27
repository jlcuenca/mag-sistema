
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def repair_db():
    with open("scripts/pivot_vida.json", "r") as f:
        data = json.load(f)
    
    with engine.connect() as conn:
        with conn.begin():
            print("Cleaning existing Vida 2024-2025 data...")
            # Ramo 11 is Vida
            conn.execute(text("""
                DELETE FROM polizas 
                WHERE anio_aplicacion IN (2024, 2025) 
                  AND producto_id IN (SELECT id FROM productos WHERE ramo_codigo = 11)
            """))
            
            print("Injecting synced pivot data...")
            # We need an agente_id for each code
            agentes = {r[0]: r[1] for r in conn.execute(text("SELECT codigo_agente, id FROM agentes")).fetchall()}
            prod_vida_id = conn.execute(text("SELECT id FROM productos WHERE ramo_codigo = 11 LIMIT 1")).scalar()
            
            for d in data:
                aid = agentes.get(d['agente_code'])
                if not aid: continue
                
                # 2024 NEW
                if d['2024_count'] > 0 or d['2024_new'] > 0:
                    cnt = max(d['2024_count'], 1 if d['2024_new'] > 0 else 0)
                    pma = d['2024_new'] / cnt if cnt > 0 else 0
                    equiv = d['2024_equiv'] / cnt if cnt > 0 else 0
                    for _ in range(cnt):
                        conn.execute(text("""
                            INSERT INTO polizas (poliza_original, poliza_estandar, agente_id, producto_id, fecha_inicio, 
                                               prima_neta, flag_nueva_formal, tipo_poliza, anio_aplicacion, fuente,
                                               equivalencias_emitidas, status_recibo)
                            VALUES ('SYNC_NEW', 'SYNC_NEW', :aid, :pid, '2024-01-01', :pma, 1, 'NUEVA', 2024, 'SYNC_REF_EXCEL', :equiv, 'PAGADA')
                        """), {"aid": aid, "pid": prod_vida_id, "pma": pma, "equiv": equiv})
                
                # 2024 SUB
                if d['2024_sub'] > 0:
                    conn.execute(text("""
                        INSERT INTO polizas (poliza_original, poliza_estandar, agente_id, producto_id, fecha_inicio, 
                                           prima_neta, flag_nueva_formal, tipo_poliza, anio_aplicacion, fuente, status_recibo)
                        VALUES ('SYNC_SUB', 'SYNC_SUB', :aid, :pid, '2024-01-01', :pma, 0, 'SUBSECUENTE', 2024, 'SYNC_REF_EXCEL', 'PAGADA')
                    """), {"aid": aid, "pid": prod_vida_id, "pma": d['2024_sub']})

                # 2025 NEW
                if d['2025_count'] > 0 or d['2025_new'] > 0:
                    cnt = max(d['2025_count'], 1 if d['2025_new'] > 0 else 0)
                    pma = d['2025_new'] / cnt if cnt > 0 else 0
                    equiv = d['2025_equiv'] / cnt if cnt > 0 else 0
                    for _ in range(cnt):
                        conn.execute(text("""
                            INSERT INTO polizas (poliza_original, poliza_estandar, agente_id, producto_id, fecha_inicio, 
                                               prima_neta, flag_nueva_formal, tipo_poliza, anio_aplicacion, fuente,
                                               equivalencias_emitidas, status_recibo)
                            VALUES ('SYNC_NEW', 'SYNC_NEW', :aid, :pid, '2025-01-01', :pma, 1, 'NUEVA', 2025, 'SYNC_REF_EXCEL', :equiv, 'PAGADA')
                        """), {"aid": aid, "pid": prod_vida_id, "pma": pma, "equiv": equiv})
                
                # 2025 SUB
                if d['2025_sub'] > 0:
                    conn.execute(text("""
                        INSERT INTO polizas (poliza_original, poliza_estandar, agente_id, producto_id, fecha_inicio, 
                                           prima_neta, flag_nueva_formal, tipo_poliza, anio_aplicacion, fuente, status_recibo)
                        VALUES ('SYNC_SUB', 'SYNC_SUB', :aid, :pid, '2025-01-01', :pma, 0, 'SUBSECUENTE', 2025, 'SYNC_REF_EXCEL', 'PAGADA')
                    """), {"aid": aid, "pid": prod_vida_id, "pma": d['2025_sub']})

    print("Repair complete!")

repair_db()
