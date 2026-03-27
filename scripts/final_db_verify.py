
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def check_dashboard_totals():
    for anio in [2024, 2025]:
        sql = f"""
            SELECT sum(prima_neta) 
            FROM polizas p
            LEFT JOIN productos pr ON p.producto_id = pr.id
            WHERE p.anio_aplicacion = {anio} AND pr.ramo_codigo = 11
        """
        with engine.connect() as conn:
            tot = conn.execute(text(sql)).scalar()
            print(f"DB Total {anio} Vida: {tot:,.2f}")
            
            # New 
            sql_new = sql + " AND (flag_nueva_formal=1 OR tipo_poliza='NUEVA')"
            tot_new = conn.execute(text(sql_new)).scalar()
            print(f"DB New {anio} Vida: {tot_new:,.2f}")

check_dashboard_totals()
