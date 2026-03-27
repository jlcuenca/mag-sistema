
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_mismatch_2025():
    # Encontrar pólizas de 2025 donde tipo_poliza (raw) era SUBSECUENTE 
    # pero flag_nueva_formal se puso en 1 (por mi motor de reglas)
    sql = """
        SELECT 
            p.poliza_original, p.fecha_inicio, p.anio_aplicacion, p.flag_nueva_formal, 
            p.tipo_poliza, p.prima_neta
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = 2025 AND pr.ramo_codigo = 11
          AND p.tipo_poliza = 'SUBSECUENTE' AND p.flag_nueva_formal = 1
        LIMIT 20
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        print("MISMATCH 2025 (Raw=SUB but Rule=NEW):")
        for r in rows:
            print(r)

check_mismatch_2025()
