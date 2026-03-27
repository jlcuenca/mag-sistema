
import os
from sqlalchemy import create_engine, text
from api.rules import aplicar_reglas_poliza
from api.database import get_db

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

def recalcular_2026():
    print("Iniciando recalculo para 2026...")
    with engine.connect() as conn:
        with conn.begin():
            # Get all 2026 policies
            polizas = conn.execute(text("""
                SELECT p.*, pr.ramo_codigo 
                FROM polizas p
                LEFT JOIN productos pr ON p.producto_id = pr.id
                WHERE p.anio_aplicacion = 2026 OR p.fecha_inicio LIKE '2026%'
            """)).mappings().all()
            
            print(f"Recalculando {len(polizas)} polizas...")
            count = 0
            for p in polizas:
                p_dict = dict(p)
                calcs = aplicar_reglas_poliza(p_dict)
                
                # Update DB
                # Just update the fields calc'd
                conn.execute(text("""
                    UPDATE polizas 
                    SET largo_poliza = :largo_poliza,
                        raiz_poliza_6 = :raiz_poliza_6,
                        terminacion = :terminacion,
                        id_compuesto = :id_compuesto,
                        es_reexpedicion = :es_reexpedicion,
                        primer_anio = :primer_anio,
                        fecha_aplicacion = :fecha_aplicacion,
                        mes_aplicacion = :mes_aplicacion,
                        pendientes_pago = :pendientes_pago,
                        trimestre = :trimestre,
                        flag_pagada = :flag_pagada,
                        flag_nueva_formal = :flag_nueva_formal,
                        tipo_poliza = :tipo_poliza_nuevo,
                        prima_anual_pesos = :prima_anual_pesos,
                        prima_acumulada_basica = :prima_acumulada_basica,
                        equivalencias_emitidas = :equivalencias_emitidas,
                        equivalencias_pagadas = :equivalencias_pagadas,
                        flag_cancelada = :flag_cancelada,
                        prima_proporcional = :prima_proporcional,
                        condicional_prima = :condicional_prima,
                        periodo_aplicacion = :periodo_aplicacion,
                        anio_aplicacion = :anio_aplicacion
                    WHERE id = :id
                """), {**calcs, "id": p['id']})
                count += 1
                if count % 100 == 0:
                    print(f"   Procesados {count}...")

    print("Recalculo masivo completado!")

if __name__ == "__main__":
    recalcular_2026()
