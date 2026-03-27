
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_lider_2024():
    # Ramo Vida = 11, Lider = 63931
    sql = """
        SELECT count(*), sum(prima_neta)
        FROM polizas p
        LEFT JOIN agentes a ON p.agente_id = a.id
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2024 AND pr.ramo_codigo = 11
          AND a.lider_codigo = '63931'
    """
    with engine.connect() as conn:
        print(f"MAG (63931) 2024: {conn.execute(text(sql)).first()}")

check_lider_2024()
