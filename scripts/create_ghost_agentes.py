
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

MISSING = ['48782', '131064', '123598', '489036', '629926', '633402', '646063', '647417', '44851', '48561']

def create_ghosts():
    with engine.connect() as conn:
        with conn.begin():
            for code in MISSING:
                conn.execute(text("""
                    INSERT INTO agentes (codigo_agente, nombre_completo, situacion) 
                    VALUES (:c, :n, 'ACTIVO')
                    ON CONFLICT (codigo_agente) DO NOTHING
                """), {"c": code, "n": f"AGENTE {code} (HIST)"})
    print("Ghosts created (safely)!")

create_ghosts()
