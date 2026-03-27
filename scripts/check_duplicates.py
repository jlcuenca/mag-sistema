
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_duplicates():
    sql = """
        SELECT poliza_original, anio_aplicacion, count(*) as c
        FROM polizas
        GROUP BY poliza_original, anio_aplicacion
        HAVING count(*) > 1
        LIMIT 20
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        print("DUPLICATES FOUND:")
        for r in rows:
            print(r)

check_duplicates()
