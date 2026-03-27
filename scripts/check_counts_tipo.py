
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_counts_2024_2025():
    sql = """
        SELECT 
            anio_aplicacion, p.tipo_poliza, count(*)
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE anio_aplicacion IN (2024, 2025) AND pr.ramo_codigo = 11
        GROUP BY anio_aplicacion, p.tipo_poliza
        ORDER BY anio_aplicacion
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        for r in rows:
            print(r)

check_counts_2024_2025()
