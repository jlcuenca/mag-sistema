
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_comision_vida_2025():
    # Vida = 11
    sql = """
        SELECT 
            CASE WHEN (comision/prima_neta) >= 0.1 THEN 'ALTA (NEW)' ELSE 'BAJA (SUB)' END as cat,
            count(*), sum(prima_neta)
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
          AND prima_neta > 0
        GROUP BY 1
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        for r in rows:
            print(r)

check_comision_vida_2025()
