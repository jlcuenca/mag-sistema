
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://mag_user:MagS1st3ma2026Gcp@34.45.14.107/mag_sistema"
engine = create_engine(DATABASE_URL)

SQL_ES_NUEVA = "(p.flag_nueva_formal=1 OR (p.flag_nueva_formal IS NULL AND p.tipo_poliza='NUEVA'))"
SQL_ES_SUBSECUENTE = "(p.flag_nueva_formal=0 OR (p.flag_nueva_formal IS NULL AND p.tipo_poliza='SUBSECUENTE'))"

def get_kpis(anio):
    sql = f"""
        SELECT 
            COUNT(CASE WHEN pr.ramo_codigo=11 AND {SQL_ES_NUEVA} THEN 1 END) as polizas_nuevas_vida,
            SUM(CASE WHEN pr.ramo_codigo=11 AND {SQL_ES_NUEVA} THEN COALESCE(p.equivalencias_emitidas, 0) ELSE 0 END) as equivalencias_vida,
            SUM(CASE WHEN pr.ramo_codigo=11 AND {SQL_ES_NUEVA} THEN COALESCE(p.prima_neta, 0) ELSE 0 END) as prima_nueva_vida,
            SUM(CASE WHEN pr.ramo_codigo=11 AND {SQL_ES_SUBSECUENTE} THEN COALESCE(p.prima_neta, 0) ELSE 0 END) as prima_sub_vida,
            SUM(CASE WHEN pr.ramo_codigo=11 THEN COALESCE(p.prima_neta, 0) ELSE 0 END) as prima_total_vida
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = :anio
    """
    with engine.connect() as conn:
        res = conn.execute(text(sql), {"anio": anio}).mappings().first()
        return res

print("--- PRODUCTION DASHBOARD KPIs ---")
for anio in [2024, 2025]:
    k = get_kpis(anio)
    print(f"\nAño {anio}:")
    print(f"  Pólizas Nuevas Vida: {k['polizas_nuevas_vida']}")
    print(f"  Equivalencias Vida:  {k['equivalencias_vida']:.2f}")
    print(f"  Prima Nueva Vida:    {k['prima_nueva_vida']:.2f}")
    print(f"  Prima Subsec. Vida:  {k['prima_sub_vida']:.2f}")
    print(f"  Prima Total Vida:    {k['prima_total_vida']:.2f}")
