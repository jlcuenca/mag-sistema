"""Verificar estado post-refactor"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from api.database import SessionLocal

db = SessionLocal()
sol = db.execute(text('SELECT COUNT(*) FROM solicitudes')).scalar()
sol_pol = db.execute(text("SELECT COUNT(*) FROM solicitudes WHERE poliza_numero IS NOT NULL")).scalar()
pol_sol = db.execute(text("SELECT COUNT(*) FROM polizas WHERE solicitud_id IS NOT NULL")).scalar()
pol = db.execute(text('SELECT COUNT(*) FROM polizas')).scalar()
etapas = db.execute(text("SELECT COUNT(*) FROM etapas_solicitudes WHERE solicitud_id IS NOT NULL")).scalar()
etapas_total = db.execute(text('SELECT COUNT(*) FROM etapas_solicitudes')).scalar()
pagos = db.execute(text('SELECT COUNT(*) FROM pagos')).scalar()

print('=== ESTADO REFACTORIZADO ===')
print(f'Solicitudes totales:     {sol:>8,}')
print(f'  con poliza vinculada:  {sol_pol:>8,} ({sol_pol/max(sol,1)*100:.1f}%)')
print(f'Polizas totales:         {pol:>8,}')
print(f'  con solicitud_id:      {pol_sol:>8,} ({pol_sol/max(pol,1)*100:.1f}%)')
print(f'Etapas totales:          {etapas_total:>8,}')
print(f'  con solicitud_id:      {etapas:>8,} ({etapas/max(etapas_total,1)*100:.1f}%)')
print(f'Pagos totales:           {pagos:>8,}')

estados = db.execute(text('SELECT estado, COUNT(*) c FROM solicitudes GROUP BY estado ORDER BY c DESC')).fetchall()
print('\nEstados:')
for e in estados:
    print(f'  {(e[0] or "SIN"):20s} {e[1]:>6,}')

ramos = db.execute(text("SELECT ramo_normalizado, COUNT(*) c FROM solicitudes WHERE ramo_normalizado IS NOT NULL GROUP BY ramo_normalizado ORDER BY c DESC")).fetchall()
print('\nRamos:')
for r in ramos:
    print(f'  {(r[0] or "SIN"):10s} {r[1]:>6,}')

db.close()
