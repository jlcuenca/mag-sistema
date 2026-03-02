"""Verificar estado de la BD después de reimportación."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from api.database import SessionLocal

db = SessionLocal()

print("=== RESUMEN BD MAG Sistema ===")
print()

total = db.execute(text("SELECT COUNT(*) FROM polizas")).scalar()
agentes = db.execute(text("SELECT COUNT(*) FROM agentes")).scalar()
productos = db.execute(text("SELECT COUNT(*) FROM productos")).scalar()
print(f"Total polizas: {total}")
print(f"Total agentes: {agentes}")
print(f"Total productos: {productos}")

print()
print("--- Por RAMO ---")
rows = db.execute(text("""
    SELECT pr.ramo_nombre, pr.ramo_codigo, COUNT(*) as cnt,
           ROUND(SUM(COALESCE(p.prima_neta, 0)), 2) as prima
    FROM polizas p JOIN productos pr ON p.producto_id = pr.id
    GROUP BY pr.ramo_nombre ORDER BY cnt DESC
""")).mappings().all()
for r in rows:
    print(f"  {r['ramo_nombre']} (Ramo {r['ramo_codigo']}): {r['cnt']} polizas, prima neta: ${r['prima']:,.0f}")

print()
print("--- Por STATUS (MyStatus) ---")
rows = db.execute(text("""
    SELECT COALESCE(mystatus, '(vacio)') as ms, COUNT(*) as cnt 
    FROM polizas GROUP BY mystatus ORDER BY cnt DESC
""")).mappings().all()
for r in rows:
    print(f"  {r['ms']}: {r['cnt']}")

print()
print("--- Por AÑO ---")
rows = db.execute(text("""
    SELECT anio_aplicacion, COUNT(*) as cnt 
    FROM polizas WHERE anio_aplicacion IS NOT NULL 
    GROUP BY anio_aplicacion ORDER BY anio_aplicacion
""")).mappings().all()
for r in rows:
    print(f"  {r['anio_aplicacion']}: {r['cnt']}")

print()
print("--- Tipo Poliza ---")
rows = db.execute(text("""
    SELECT COALESCE(tipo_poliza, '(sin clasificar)') as tp, COUNT(*) as cnt 
    FROM polizas GROUP BY tipo_poliza ORDER BY cnt DESC
""")).mappings().all()
for r in rows:
    print(f"  {r['tp']}: {r['cnt']}")

print()
print("--- Reglas calculadas (muestra) ---")
rows = db.execute(text("""
    SELECT poliza_original, largo_poliza, raiz_poliza_6, terminacion, primer_anio, trimestre, 
           flag_pagada, flag_nueva_formal, prima_anual_pesos, equivalencias_emitidas, flag_cancelada
    FROM polizas WHERE prima_neta > 0 AND flag_pagada = 1 LIMIT 5
""")).mappings().all()
for r in rows:
    print(f"  {r['poliza_original']}: largo={r['largo_poliza']}, raiz6={r['raiz_poliza_6']}, "
          f"term={r['terminacion']}, PA={r['primer_anio']}, Q={r['trimestre']}, "
          f"pag={r['flag_pagada']}, nueva={r['flag_nueva_formal']}, "
          f"pesos=${r['prima_anual_pesos']:,.0f}, equiv={r['equivalencias_emitidas']}, "
          f"canc={r['flag_cancelada']}")

print()
print("--- Reglas: Distribucion flag_pagada ---")
rows = db.execute(text("""
    SELECT flag_pagada, COUNT(*) as cnt FROM polizas GROUP BY flag_pagada
""")).mappings().all()
for r in rows:
    print(f"  flag_pagada={r['flag_pagada']}: {r['cnt']}")

print()
print("--- Reglas: Distribucion flag_cancelada ---")
rows = db.execute(text("""
    SELECT flag_cancelada, COUNT(*) as cnt FROM polizas GROUP BY flag_cancelada
""")).mappings().all()
for r in rows:
    print(f"  flag_cancelada={r['flag_cancelada']}: {r['cnt']}")

db.close()
print()
print("=== VERIFICACION COMPLETA ===")
