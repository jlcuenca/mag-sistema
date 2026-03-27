
import os
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

with open("scripts/pivot_vida.json", "r") as f:
    data = json.load(f)

with engine.connect() as conn:
    existing = {r[0] for r in conn.execute(text("SELECT codigo_agente FROM agentes")).fetchall()}
    missing = [d['agente_code'] for d in data if d['agente_code'] not in existing]
    print(f"Missing agents ({len(missing)}): {missing}")
