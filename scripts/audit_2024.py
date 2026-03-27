
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def audit_2024():
    sql = """
        SELECT 
            p.poliza_original, p.fecha_inicio, p.anio_aplicacion, p.flag_nueva_formal, 
            p.tipo_poliza, p.prima_neta
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2024 AND pr.ramo_codigo = 11
        LIMIT 50
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        print("SAMPLE 2024 POLICIES:")
        for r in rows:
            print(r)

audit_2024()
