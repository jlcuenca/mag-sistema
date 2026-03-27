
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_pol_len():
    sql = "SELECT poliza_original FROM polizas WHERE anio_aplicacion = 2025 AND ramo_codigo = 11 LIMIT 10"
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        for r in rows:
            print(f"'{r[0]}' len={len(r[0])}")

check_pol_len()
