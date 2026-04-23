import os
import sys
import time
from datetime import datetime

# Agregar el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import text
from api.database import SessionLocal, Solicitud, EtapaSolicitud
from api.oracle_client import get_oracle_connection

def main():
    print("🚀 Iniciando importación de Solicitudes/Etapas desde Oracle (VW_CONCENTRADO_ULT_ETAPAS)...")
    start_time = time.time()
    
    db = SessionLocal()
    oracle_conn = None
    
    try:
        oracle_conn = get_oracle_connection()
        cursor = oracle_conn.cursor()
        
        # 1. Consultar vista
        print("📥 Extrayendo últimas etapas...")
        query = "SELECT * FROM UCARTERA.VW_CONCENTRADO_ULT_ETAPAS"
        cursor.execute(query)
        
        columns = [col[0] for col in cursor.description]
        
        total = 0
        batch_solicitudes = []
        
        for row in cursor:
            data = dict(zip(columns, row))
            
            nosol = str(data.get("NOSOL") or "")
            if not nosol:
                continue
                
            # Mapeo a Solicitud
            sol_map = {
                "nosol": nosol,
                "nomramo": data.get("NOMRAMO") or data.get("RAMO"),
                "contratante_nombre": data.get("CONTRATANTE"),
                "idagente": str(data.get("IDAGENTE") or ""),
                "ultima_etapa": data.get("ETAPA"),
                "ultima_subetapa": data.get("SUBETAPA"),
                "fecha_ultima_etapa": str(data.get("FECETAPA") or "")[:10],
                "fuente": "ORACLE_VW_CONCENTRADO",
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert logic (simplificada: borrar y reinsertar o actualizar si existe)
            # Para simplificar este script de 'insumo', usaremos inserción directa
            # En un entorno real, usaríamos ON CONFLICT DO UPDATE (PostgreSQL)
            
            batch_solicitudes.append(sol_map)
            total += 1
            
            if len(batch_solicitudes) >= 1000:
                # Nota: En SQLite/PostgreSQL local, esto es más rápido con core
                for item in batch_solicitudes:
                    # Intento de actualización simple
                    existing = db.query(Solicitud).filter_by(nosol=item["nosol"]).first()
                    if existing:
                        for key, value in item.items():
                            setattr(existing, key, value)
                    else:
                        db.add(Solicitud(**item))
                
                db.commit()
                print(f"   ⏳ {total:,} solicitudes procesadas...", end="\r")
                batch_solicitudes = []
                
        if batch_solicitudes:
            for item in batch_solicitudes:
                existing = db.query(Solicitud).filter_by(nosol=item["nosol"]).first()
                if existing:
                    for key, value in item.items():
                        setattr(existing, key, value)
                else:
                    db.add(Solicitud(**item))
            db.commit()
            
        print(f"\n✅ Importación completada: {total:,} solicitudes actualizadas en {time.time() - start_time:.1f}s")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        if oracle_conn:
            oracle_conn.close()
        db.close()

if __name__ == "__main__":
    main()
