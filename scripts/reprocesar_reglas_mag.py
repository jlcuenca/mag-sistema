
import sys
import os
import time
from datetime import datetime
from sqlalchemy import text

# Agregar el directorio raíz al path para importar api
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from api.database import engine, SessionLocal, Poliza
from api.rules import aplicar_reglas_batch

def main():
    inicio = time.time()
    print("=" * 80)
    print("  MAG Sistema — Reprocesamiento de Reglas de Negocio")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Leer todas las pólizas con sus datos de producto
        print("\n[1/3] Leyendo pólizas desde la base de datos...")
        rows = db.execute(text("""
            SELECT p.*, pr.ramo_codigo, pr.ramo_nombre
            FROM polizas p
            LEFT JOIN productos pr ON p.producto_id = pr.id
        """)).mappings().all()

        polizas_dicts = [dict(r) for r in rows]
        total_p = len(polizas_dicts)
        print(f"  ✅ {total_p} pólizas cargadas para análisis.")

        # 2. Aplicar motor de reglas (v.0.2.5+)
        print("\n[2/3] Aplicando motor de reglas actualizado...")
        resultados = aplicar_reglas_batch(polizas_dicts)
        print("  ✅ Reglas calculadas exitosamente.")

        # 3. Actualizar registros en base de datos
        print("\n[3/3] Persistiendo cambios en la base de datos (batch mode)...")
        actualizados = 0
        batch_size = 500
        current_batch = []

        # SQL de actualización masiva con los nuevos campos
        update_sql = text("""
            UPDATE polizas SET
                largo_poliza = :largo,
                raiz_poliza_6 = :raiz6,
                terminacion = :term,
                num_reexpediciones = :nreexp,
                id_compuesto = :id_comp,
                es_reexpedicion = :reexp,
                primer_anio = :primer,
                fecha_aplicacion = :fec_apli,
                mes_aplicacion = :mes_apli,
                pendientes_pago = :pend,
                trimestre = :trim,
                flag_pagada = :fpag,
                flag_nueva_formal = :fnueva,
                tipo_poliza = :tipo,
                prima_anual_pesos = :pap,
                equivalencias_emitidas = :eqe,
                equivalencias_pagadas = :eqp,
                flag_cancelada = :fcanc,
                prima_proporcional = :pprop,
                condicional_prima = :cprim,
                prima_acumulada_basica = :pacum,
                updated_at = :now
            WHERE id = :id
        """)

        for i, (poliza_dict, reglas) in enumerate(zip(polizas_dicts, resultados)):
            current_batch.append({
                "id": poliza_dict["id"],
                "largo": reglas.get("largo_poliza"),
                "raiz6": reglas.get("raiz_poliza_6"),
                "term": reglas.get("terminacion"),
                "nreexp": reglas.get("num_reexpediciones"),
                "id_comp": reglas.get("id_compuesto"),
                "reexp": reglas.get("es_reexpedicion"),
                "primer": reglas.get("primer_anio"),
                "fec_apli": reglas.get("fecha_aplicacion"),
                "mes_apli": reglas.get("mes_aplicacion"),
                "pend": reglas.get("pendientes_pago"),
                "trim": reglas.get("trimestre"),
                "fpag": reglas.get("flag_pagada"),
                "fnueva": reglas.get("flag_nueva_formal"),
                "tipo": reglas.get("tipo_poliza_nuevo"),
                "pap": reglas.get("prima_anual_pesos"),
                "eqe": reglas.get("equivalencias_emitidas"),
                "eqp": reglas.get("equivalencias_pagadas"),
                "fcanc": reglas.get("flag_cancelada"),
                "pprop": reglas.get("prima_proporcional"),
                "cprim": reglas.get("condicional_prima"),
                "pacum": reglas.get("prima_acumulada_basica"),
                "now": datetime.now().isoformat(),
            })

            if len(current_batch) >= batch_size:
                db.execute(update_sql, current_batch)
                db.flush()
                actualizados += len(current_batch)
                print(f"     ... {actualizados}/{total_p} registros actualizados")
                current_batch = []

        if current_batch:
            db.execute(update_sql, current_batch)
            actualizados += len(current_batch)

        db.commit()
        
        # 4. Resumen final
        print(f"\n  ✅ {actualizados} pólizas actualizadas correctamente.")
        print("-" * 40)
        print(f"  Pólizas totales: {total_p}")
        print(f"  Tiempo transcurrido: {time.time() - inicio:.1f} segundos")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
