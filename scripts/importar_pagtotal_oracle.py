import os
import sys
import time
from datetime import datetime

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, Pago
from api.oracle_client import get_oracle_connection

def main():
    print("🚀 Iniciando importación de PAGTOTAL desde Oracle...")
    start_time = time.time()
    
    db = SessionLocal()
    oracle_conn = None
    
    try:
        oracle_conn = get_oracle_connection()
        cursor = oracle_conn.cursor()
        
        # 1. Consultar datos con filtros solicitados
        # - FECAPLI >= SYSDATE-5
        # - Excluyendo ramos de autos (asumo RAMO no en (listado de autos))
        # Nota: Ajustar nombres de columnas si varían en Oracle
        print("📥 Extrayendo pagos de los últimos 5 días...")
        
        query = """
            SELECT * FROM PAGTOTAL 
            WHERE FECAPLI >= SYSDATE - 5
            AND RAMO NOT LIKE '%AUTO%' 
            AND RAMO NOT IN ('AUTOS', 'MOTOS')
        """
        cursor.execute(query)
        
        columns = [col[0] for col in cursor.description]
        
        batch = []
        BATCH_SIZE = 2000
        total = 0
        
        for row in cursor:
            data = dict(zip(columns, row))
            
            pago_map = {
                "poliza_numero": str(data.get("POLIZA") or ""),
                "endoso": str(data.get("ENDOSO") or ""),
                "agente_codigo": str(data.get("AGENTE") or ""),
                "contratante": data.get("CONTRATANTE"),
                "ramo": data.get("RAMO"),
                "moneda": data.get("MON") or data.get("MONEDA") or "MN",
                "fecha_inicio": str(data.get("PERINI") or "")[:10],
                "fecha_aplicacion": str(data.get("FECAPLI") or "")[:10],
                "comprobante": data.get("COMPROBANTE"),
                "prima_neta": float(data.get("NETA") or 0),
                "prima_total": float(data.get("PRITOT") or data.get("TOTAL") or 0),
                "comision": float(data.get("COMISION") or 0),
                "comision_total": float(data.get("TOTCOMISION") or 0),
                "poliza_match": str(data.get("POLIZA") or ""),
                "fuente": "ORACLE_PAGTOTAL",
                "created_at": datetime.now().isoformat()
            }
            
            if pago_map["poliza_numero"]:
                batch.append(pago_map)
                total += 1
                
            if len(batch) >= BATCH_SIZE:
                db.execute(Pago.__table__.insert(), batch)
                db.commit()
                print(f"   ⏳ {total:,} pagos procesados...", end="\r")
                batch = []
                
        if batch:
            db.execute(Pago.__table__.insert(), batch)
            db.commit()
            
        print(f"\n✅ Importación completada: {total:,} pagos en {time.time() - start_time:.1f}s")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        if oracle_conn:
            oracle_conn.close()
        db.close()

if __name__ == "__main__":
    main()
