
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_agents_2024():
    sql = """
        SELECT a.nombre_completo, count(*)
        FROM polizas p
        JOIN agentes a ON p.agente_id = a.id
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2024 AND pr.ramo_codigo = 11
        GROUP BY a.nombre_completo
        ORDER BY count(*) DESC
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        for r in rows:
            print(r)

check_agents_2024()
