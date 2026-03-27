
import os
import json
from sqlalchemy import create_engine, text
from api.rules import aplicar_reglas_poliza
from api.database import Poliza, Producto, Agente

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def debug_poliza(numero):
    with engine.connect() as conn:
        # Fetch raw data
        res = conn.execute(text("""
            SELECT p.*, pr.ramo_codigo, pr.ramo_nombre, pr.plan, a.nombre_completo as agente_nombre
            FROM polizas p
            LEFT JOIN productos pr ON p.producto_id = pr.id
            LEFT JOIN agentes a ON p.agente_id = a.id
            WHERE p.poliza_original = :n OR p.poliza_estandar = :n
        """), {"n": numero}).mappings().all()
        
        if not res:
            print(f"Poliza {numero} no encontrada.")
            return

        for row in res:
            print(f"\n=== [ DATOS DE INSUMO (BD) - POLIZA {row['poliza_original']} ] ===")
            for k, v in row.items():
                print(f"{k:30}: {v}")
            
            # Apply rules again for debugging
            pol_dict = dict(row)
            # Fetch prima_acumulada if not in row
            # ...
            
            calculated = aplicar_reglas_poliza(pol_dict)
            print(f"\n=== [ REGLAS DE NEGOCIO CALCULADAS ] ===")
            for k, v in calculated.items():
                print(f"{k:30}: {v}")

debug_poliza("1072723H")
