"""
Fix: Corregir ramo_codigo de productos de automóviles.
=====================================================
Problema: Las pólizas de automóviles fueron importadas con ramo_codigo=34 (GMM)
en lugar de ramo_codigo=90 (AUTOS). El ramo_nombre sí dice "Individual Automoviles"
y el plan dice "AUTO", pero el código numérico está mal.

Esto se puede detectar fácilmente:
- ramo_nombre contiene "Automovil" o "Auto" → ramo_codigo debería ser 90
- plan = "AUTO" → ramo_codigo debería ser 90

Solución: UPDATE productos SET ramo_codigo=90 WHERE plan='AUTO' OR ramo_nombre LIKE '%utomovil%'
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# Usar la URL de Cloud SQL desde variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL no configurada.")
    print("  En Cloud Shell: export DATABASE_URL='postgresql://mag_user:PASSWORD@/mag_sistema?host=/cloudsql/magia-mag:us-central1:mag-db'")
    sys.exit(1)

print(f"Conectando a: {DATABASE_URL.split('@')[0]}@...")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # 1. Diagnóstico: ver productos actuales con sus ramos
    print("\n=== DIAGNÓSTICO: Productos con plan AUTO ===")
    rows = db.execute(text("""
        SELECT id, ramo_codigo, ramo_nombre, plan, gama
        FROM productos
        WHERE UPPER(plan) = 'AUTO'
           OR LOWER(ramo_nombre) LIKE '%automovil%'
           OR LOWER(ramo_nombre) LIKE '%automóvil%'
        ORDER BY id
    """)).mappings().all()

    for r in rows:
        flag = "❌ MAL" if r["ramo_codigo"] != 90 else "✅ OK"
        print(f"  {flag} id={r['id']} ramo_codigo={r['ramo_codigo']} "
              f"ramo_nombre={r['ramo_nombre']} plan={r['plan']} gama={r['gama']}")

    if not rows:
        print("  No se encontraron productos de automóviles.")
        sys.exit(0)

    wrong = [r for r in rows if r["ramo_codigo"] != 90]
    print(f"\n  Total productos auto: {len(rows)}")
    print(f"  Con ramo_codigo incorrecto: {len(wrong)}")

    if not wrong:
        print("  ✅ Todos los productos de autos ya tienen ramo_codigo=90")
        sys.exit(0)

    # 2. Contar pólizas afectadas
    affected = db.execute(text("""
        SELECT COUNT(*) FROM polizas p
        JOIN productos pr ON p.producto_id = pr.id
        WHERE (UPPER(pr.plan) = 'AUTO'
               OR LOWER(pr.ramo_nombre) LIKE '%automovil%'
               OR LOWER(pr.ramo_nombre) LIKE '%automóvil%')
          AND pr.ramo_codigo != 90
    """)).scalar()
    print(f"  Pólizas afectadas: {affected}")

    # 3. Corregir el ramo_codigo en productos
    print("\n=== APLICANDO CORRECCIÓN ===")
    updated = db.execute(text("""
        UPDATE productos
        SET ramo_codigo = 90
        WHERE (UPPER(plan) = 'AUTO'
               OR LOWER(ramo_nombre) LIKE '%automovil%'
               OR LOWER(ramo_nombre) LIKE '%automóvil%')
          AND ramo_codigo != 90
    """)).rowcount
    db.commit()
    print(f"  ✅ {updated} productos actualizados a ramo_codigo=90")

    # 4. Verificación
    print("\n=== VERIFICACIÓN POST-FIX ===")
    verify = db.execute(text("""
        SELECT pr.ramo_codigo, pr.ramo_nombre, COUNT(*) as total_polizas,
               ROUND(CAST(SUM(COALESCE(p.prima_neta, 0)) AS NUMERIC), 2) as prima_total
        FROM polizas p
        JOIN productos pr ON p.producto_id = pr.id
        GROUP BY pr.ramo_codigo, pr.ramo_nombre
        ORDER BY total_polizas DESC
    """)).mappings().all()

    print(f"  {'Código':>6}  {'Ramo':<30}  {'Pólizas':>8}  {'Prima Neta':>15}")
    print(f"  {'─'*6}  {'─'*30}  {'─'*8}  {'─'*15}")
    for r in verify:
        print(f"  {r['ramo_codigo']:>6}  {(r['ramo_nombre'] or ''):<30}  "
              f"{r['total_polizas']:>8}  ${r['prima_total']:>14,.2f}")

    print("\n✅ Corrección completada exitosamente")

except Exception as e:
    db.rollback()
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
