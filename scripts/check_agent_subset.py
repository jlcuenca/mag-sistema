
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

AGENT_CODES = ['644717', '625328', '629094', '48561', '47968', '645658', '646069', '633890', '647749', '48357', '631611', '55538', '48847', '622011']

def check_agent_subset():
    sql = """
        SELECT count(*), sum(prima_neta)
        FROM polizas p
        JOIN agentes a ON p.agente_id = a.id
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
          AND a.codigo_agente IN :codes
    """
    with engine.connect() as conn:
        print(f"Subset results: {conn.execute(text(sql), {'codes': tuple(AGENT_CODES)}).first()}")

check_agent_subset()
