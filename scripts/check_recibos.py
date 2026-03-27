
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_recibos_2025():
    # Vida = 11
    sql = """
        SELECT count(*)
        FROM recibos r
        JOIN polizas p ON r.poliza_id = p.id
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
    """
    with engine.connect() as conn:
        print(f"Recibos count for 2025 Vida: {conn.execute(text(sql)).scalar()}")

check_recibos_2025()
