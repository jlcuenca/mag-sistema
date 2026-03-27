
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_comision_raw():
    sql = """
        SELECT count(*), count(comision), sum(COALESCE(comision,0))
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
    """
    with engine.connect() as conn:
        print(conn.execute(text(sql)).first())

check_comision_raw()
