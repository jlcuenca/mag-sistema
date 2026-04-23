import os
import sys
import time
from datetime import datetime

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, engine, Poliza
from api.oracle_client import get_oracle_connection

def main():
    print("🚀 Iniciando importación del Maestro de Pólizas (Oracle)...")
    start_time = time.time()
    
    db = SessionLocal()
    oracle_conn = None
    
    try:
        # 1. Conectar a Oracle
        oracle_conn = get_oracle_connection(thick_mode=False) # Intentar Thin primero
        cursor = oracle_conn.cursor()
        
        # 2. Consultar datos
        # Nota: UCARTERA.POLIZAS_01
        print("📥 Extrayendo datos de UCARTERA.POLIZAS_01...")
        query = "SELECT * FROM UCARTERA.POLIZAS_01"
        cursor.execute(query)
        
        columns = [col[0] for col in cursor.description]
        print(f"✅ Columnas encontradas: {len(columns)}")
        
        # 3. Limpiar tabla local (opcional, según requerimiento de 'descarga completa')
        print("🗑️ Limpiando tabla local 'polizas'...")
        db.execute(text("DELETE FROM polizas"))
        db.commit()
        
        # 4. Insertar en batches
        batch = []
        BATCH_SIZE = 5000
        total = 0
        
        # Mapeo sugerido (ajustar según nombres reales en Oracle)
        # Aquí asumo algunos nombres comunes, pero el script es flexible
        for row in cursor:
            data = dict(zip(columns, row))
            
            # Mapeo a modelo Poliza
            poliza_map = {
                "poliza_original": str(data.get("POLIZA") or data.get("POLIZA_ORIGINAL") or ""),
                "poliza_estandar": str(data.get("POLIZA_ESTANDAR") or data.get("POLIZA") or ""),
                "asegurado_nombre": data.get("ASEGURADO") or data.get("NOMBRE_ASEGURADO"),
                "contratante_nombre": data.get("CONTRATANTE"),
                "fecha_inicio": str(data.get("FECHA_INICIO") or data.get("FECINI") or "")[:10],
                "fecha_emision": str(data.get("FECHA_EMISION") or data.get("FECEMI") or "")[:10],
                "ramo": data.get("RAMO"),
                "moneda": data.get("MONEDA") or "MN",
                "prima_neta": float(data.get("PRIMA_NETA") or data.get("NETA") or 0),
                "prima_total": float(data.get("PRIMA_TOTAL") or data.get("TOTAL") or 0),
                "fuente": "ORACLE_MAESTRO",
                "updated_at": datetime.now().isoformat()
            }
            
            # Solo insertar si tiene número de póliza
            if poliza_map["poliza_original"]:
                batch.append(poliza_map)
                total += 1
            
            if len(batch) >= BATCH_SIZE:
                # Inserción rápida usando SQLAlchemy Core
                db.execute(Poliza.__table__.insert(), batch)
                db.commit()
                print(f"   ⏳ {total:,} registros procesados...", end="\r")
                batch = []
        
        if batch:
            db.execute(Poliza.__table__.insert(), batch)
            db.commit()
            
        end_time = time.time()
        print(f"\n✅ Importación completada: {total:,} pólizas en {end_time - start_time:.1f}s")
        
    except Exception as e:
        print(f"\n❌ Error durante la importación: {e}")
        db.rollback()
    finally:
        if oracle_conn:
            oracle_conn.close()
        db.close()

if __name__ == "__main__":
    main()
