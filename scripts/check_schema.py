
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_schema():
    sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'polizas'
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        for r in rows:
            print(r)

check_schema()
