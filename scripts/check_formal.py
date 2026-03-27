
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_formal_2025():
    sql = """
        SELECT count(*)
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
          AND p.flag_nueva_formal = 1
    """
    with engine.connect() as conn:
        print(f"Formal policies in 2025: {conn.execute(text(sql)).scalar()}")

check_formal_2025()
