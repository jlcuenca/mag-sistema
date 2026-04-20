"""
Motor de Reglas de Negocio ICP 2026 (Incentivos y Convenciones Promotor)
v1.0.0 — Implementación de reglas basadas en ref/ICP 2026.pdf
"""
from datetime import date, datetime
from typing import Dict, Any, List

# ── CONFIGURACIÓN DE METAS 2026 (Pág. 3 del PDF) ─────────────────────
METAS_ICP_2026 = {
    "PEQUENA": {  # Hasta 250 mdp
        "recluta_productiva": 3,
        "polizas_vida_individual": 100,
        "agentes_alfa_camino1": 2,  # Adicionales vs Dic 2025
        "agentes_alfa_camino2_pct": 0.10,
        "asegurados_gmmi": 250,
        "crecimiento_cartera_pct": 0.10,
        "agentes_ganadores_bono": 15
    },
    "MEDIANA": {  # >250 mdp y <500 mdp
        "recluta_productiva": 5,
        "polizas_vida_individual": 200,
        "agentes_alfa_camino1": 4,
        "agentes_alfa_camino2_pct": 0.10,
        "asegurados_gmmi": 500,
        "crecimiento_cartera_pct": 0.10,
        "agentes_ganadores_bono": 30
    },
    "GRANDE": {  # >= 500 mdp
        "recluta_productiva": 8,
        "polizas_vida_individual": 300,
        "agentes_alfa_camino1": 5,
        "agentes_alfa_camino2_pct": 0.10,
        "asegurados_gmmi": 1000,
        "crecimiento_cartera_pct": 0.10,
        "agentes_ganadores_bono": 70
    }
}

# ── REGLA 01: Multiplicadores Vida Individual (Pág. 7 del PDF) ────────
def calcular_puntos_vida_2026(prima_neta_anual: float) -> int:
    """
    Calcula el factor multiplicador para el conteo de pólizas nuevas de Vida.
    Monto de prima anual por póliza:
    - >= 100,000 -> 3
    - >= 50,000 y < 100,000 -> 2
    - >= 16,000 y < 50,000 -> 1
    - < 16,000 -> 0 (no contabiliza según tabla, aunque en la práctica suele ser 0.5 o 0)
    """
    if prima_neta_anual >= 100000:
        return 3
    elif prima_neta_anual >= 50000:
        return 2
    elif prima_neta_anual >= 16000:
        return 1
    return 0

# ── REGLA 02: Clasificación de Cartera (Pág. 3 del PDF) ──────────────
def clasificar_tamano_cartera(prima_pagada_total: float) -> str:
    """Retorna la categoría de la promotoría según su cartera en millones de pesos (mdp)."""
    # El PDF habla de mdp (millones de pesos)
    if prima_pagada_total >= 500_000_000:
        return "GRANDE"
    elif prima_pagada_total >= 250_000_000:
        return "MEDIANA"
    return "PEQUENA"

# ── REGLA 03: Recluta Productiva (Pág. 5-6 del PDF) ───────────────────
def es_eligibilidad_recluta_2026(fecha_alta_agente: str) -> bool:
    """
    Un agente es elegible para Recluta Productiva si:
    - Tiene máximo 3 años contados desde su alta.
    Años definidos en el PDF:
    - Año 1: 1 jul 2025 al 31 dic 2026
    - Año 2: 1 ene 2024 al 30 jun 2025
    - Año 3: 1 ene 2023 al 31 dic 2023
    """
    if not fecha_alta_agente:
        return False
    try:
        f_alta = datetime.strptime(fecha_alta_agente[:10], "%Y-%m-%d").date()
        cutoff = date(2023, 1, 1)
        return f_alta >= cutoff
    except (ValueError, TypeError):
        return False

def check_recluta_productiva_camino1(polizas_vida: int, prima_pagada: float, antiguedad_anio: int) -> bool:
    """
    Camino 1: Requisitos de Vida Individual 1er Año + Salud Individual 1er Año + Planmed.
    (Pág. 5)
    Antigüedad Año 1: 9 pólizas (mín 3 Vida) Y 200,000 prima.
    Antigüedad Año 2: 12 pólizas (mín 4 Vida) Y 300,000 prima.
    Antigüedad Año 3: 15 pólizas (mín 5 Vida) Y 400,000 prima.
    """
    metas = {
        1: {"polizas": 9, "vida": 3, "prima": 200000},
        2: {"polizas": 12, "vida": 4, "prima": 300000},
        3: {"polizas": 15, "vida": 5, "prima": 400000}
    }
    m = metas.get(antiguedad_anio)
    if not m: return False
    
    return polizas_vida >= m["vida"] and prima_pagada >= m["prima"]

# ── REGLA 04: Crecimiento de Cartera (Pág. 10 del PDF) ────────────────
def calcular_pct_crecimiento(prima_actual_12m: float, prima_anterior_12m: float) -> float:
    """Fórmula: (Prima 2026 / Prima 2025) - 1"""
    if prima_anterior_12m <= 0:
        return 0.0
    return (prima_actual_12m / prima_anterior_12m) - 1

# ── REGLA 05: Siniestralidad (Pág. 11 del PDF) ────────────────────────
def calcular_siniestralidad(siniestros_12m: float, prima_pagada_12m: float) -> float:
    """Fórmula: Siniestros Ocurridos / Prima Neta Pagada y Aplicada"""
    if prima_pagada_12m <= 0:
        return 0.0
    return siniestros_12m / prima_pagada_12m

# ── EVALUADOR DE SEGMENTO 2026 (Pág. 4 del PDF) ─────────────────────
def evaluar_segmento_icp_2026(indicadores_cumplidos: List[str]) -> str:
    """
    Determina el segmento basado en el cumplimiento de los 6 indicadores básicos.
    Requisito indispensable para ALFA/ALFA+: Haber cumplido 'Recluta Productiva'.
    
    Indicadores:
    1. Recluta Productiva
    2. Pólizas nuevas Vida Individual
    3. Agentes Alfa
    4. Asegurados nuevos GMMI
    5. Crecimiento de cartera
    6. Agentes ganadores de bono
    """
    num_cumplidos = len(indicadores_cumplidos)
    tiene_recluta = "recluta_productiva" in indicadores_cumplidos
    
    # Haber cumplido Agentes Alfa (Cualquiera de los 2 caminos)
    tiene_alfa = "agentes_alfa" in indicadores_cumplidos or "agentes_alfa_pct" in indicadores_cumplidos
    
    # Para ALFA/ALFA+: Indispensable Recluta + Alfa
    if num_cumplidos >= 5:
        return "ALFA+" if (tiene_recluta and tiene_alfa) else "OMEGA+"
    elif num_cumplidos >= 3:
        return "ALFA" if (tiene_recluta and tiene_alfa) else "OMEGA+"
    elif num_cumplidos >= 1:
        return "OMEGA+"
    
    return "OMEGA"

# ── REGLA: Bonos de Calidad (Pág. 11-13 del PDF) ────────────────────

def evaluar_bono_calidad(persistencia: float, siniestralidad: float) -> Dict[str, Any]:
    """
    Calcula el multiplicador del bono basado en calidad.
    Bono Persistencia: >= 89% (100%), 85-88% (50%), <85% (0%)
    Bono Siniestralidad: <= 55% (100%), 56-65% (50%), >65% (0%)
    """
    # Persistencia
    pct_pers = 0.0
    if persistencia >= 0.89:
        pct_pers = 1.0
    elif persistencia >= 0.85:
        pct_pers = 0.5
        
    # Siniestralidad (Inversa)
    pct_sini = 0.0
    if siniestralidad <= 0.55:
        pct_sini = 1.0
    elif siniestralidad <= 0.65:
        pct_sini = 0.5
        
    return {
        "persistencia_pct": pct_pers,
        "siniestralidad_pct": pct_sini,
        "total_calidad_pct": (pct_pers + pct_sini) / 2, # Promedio de cumplimiento
        "aplica_bono": pct_pers > 0 and pct_sini > 0
    }

# ── RESUMEN DE STATUS ICP 2026 ──────────────────────────────────────
def generar_resumen_icp_2026(data_actual: Dict[str, Any], tamano_cartera: str) -> Dict[str, Any]:
    """Genera el resumen completo de indicadores y segmento."""
    config = METAS_ICP_2026.get(tamano_cartera, METAS_ICP_2026["PEQUENA"])
    
    # Mapeo de indicadores base
    mapeo = [
        {"id": 1, "key": "recluta_productiva", "name": "Recluta Productiva", "meta": config["recluta_productiva"]},
        {"id": 2, "key": "polizas_vida_individual", "name": "Vida Individual (Puntos)", "meta": config["polizas_vida_individual"]},
        {"id": 3, "key": "agentes_alfa_adicionales", "name": "Agentes Alfa (Adicionales)", "meta": config["agentes_alfa_camino1"]},
        {"id": 3, "key": "agentes_alfa_pct_actual", "name": "Agentes Alfa (% Fuerza Vtas)", "meta": config["agentes_alfa_camino2_pct"]},
        {"id": 4, "key": "asegurados_gmmi", "name": "Asegurados nuevos GMMI", "meta": config["asegurados_gmmi"]},
        {"id": 5, "key": "crecimiento_cartera_pct", "name": "Crecimiento de cartera", "meta": config["crecimiento_cartera_pct"]},
        {"id": 6, "key": "agentes_ganadores_bono", "name": "Agentes ganadores de bono", "meta": config["agentes_ganadores_bono"]},
    ]
    
    indicadores_out = []
    cumplidos_keys = []
    
    for m in mapeo:
        val = data_actual.get(m["key"], 0)
        meta = m["meta"]
        
        # Formateo si es porcentaje
        is_pct = "pct" in m["key"]
        
        cumple = val >= meta
        if cumple:
            cumplidos_keys.append(m["key"].replace("_pct", ""))
            
        indicadores_out.append({
            "id": m["id"],
            "nombre": m["name"],
            "actual": f"{val*100:.1f}%" if is_pct else str(val),
            "meta": f"{meta*100:.1f}%" if is_pct else str(meta),
            "cumple": cumple
        })
    
    # Mapeo invertido para evaluar segmento
    # (El evaluador espera nombres específicos)
    indicadores_eval = []
    if data_actual.get("recluta_productiva", 0) >= config["recluta_productiva"]: indicators_key = "recluta_productiva"; indicadores_eval.append(indicators_key)
    if data_actual.get("polizas_vida_individual", 0) >= config["polizas_vida_individual"]: indicadores_eval.append("polizas_vida_individual")
    if data_actual.get("agentes_alfa_adicionales", 0) >= config["agentes_alfa_camino1"]: indicadores_eval.append("agentes_alfa")
    if data_actual.get("agentes_alfa_pct_actual", 0) >= config["agentes_alfa_camino2_pct"]: indicadores_eval.append("agentes_alfa_pct")
    if data_actual.get("asegurados_gmmi", 0) >= config["asegurados_gmmi"]: indicadores_eval.append("asegurados_gmmi")
    if data_actual.get("crecimiento_cartera_pct", 0) >= config["crecimiento_cartera_pct"]: indicadores_eval.append("crecimiento_cartera")
    if data_actual.get("agentes_ganadores_bono", 0) >= config["agentes_ganadores_bono"]: indicadores_eval.append("agentes_ganadores_bono")

    segmento = evaluar_segmento_icp_2026(indicadores_eval)
    
    # Calidad (Simulada por ahora con datos base)
    persistencia = data_actual.get("persistencia", 0.92) # Mock 92%
    siniestralidad = data_actual.get("siniestralidad", 0.48) # Mock 48%
    calidad = evaluar_bono_calidad(persistencia, siniestralidad)
    
    return {
        "cartera_categoria": tamano_cartera,
        "segmento_alcanzado": segmento,
        "total_cumplidos": len(indicadores_eval),
        "indicadores": indicadores_out,
        "persistencia_actual": float(persistencia),
        "siniestralidad_actual": float(siniestralidad),
        "bono_calidad_aplica": calidad["aplica_bono"]
    }

def obtener_detalle_recluta_2026(agentes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Procesa una lista de agentes y determina su estatus detallado de Recluta Productiva.
    """
    detalle = []
    hoy = date.today()
    
    for a in agentes_data:
        # Calcular año de antigüedad (1, 2 o 3)
        alta_str = a.get("fecha_alta")
        if not alta_str: continue
        
        alta = datetime.strptime(alta_str[:10], "%Y-%m-%d").date()
        
        # Lógica simplificada de años según PDF
        if alta >= date(2025, 7, 1): anio_antiguedad = 1
        elif alta >= date(2024, 1, 1): anio_antiguedad = 2
        elif alta >= date(2023, 1, 1): anio_antiguedad = 3
        else: continue # No califica como recluta 2026
        
        meta = {
            1: {"polizas": 9, "vida": 3, "prima": 200000},
            2: {"polizas": 12, "vida": 4, "prima": 300000},
            3: {"polizas": 15, "vida": 5, "prima": 400000}
        }.get(anio_antiguedad)
        
        polizas_tot = a.get("polizas_total", 0)
        polizas_vida = a.get("polizas_vida", 0)
        prima = a.get("prima_total", 0)
        
        cumple = polizas_vida >= meta["vida"] and prima >= meta["prima"]
        
        detalle.append({
            "agente_id": a.get("id"),
            "nombre": a.get("nombre_completo"),
            "codigo": a.get("codigo_agente"),
            "fecha_alta": alta_str,
            "anio_icp": anio_antiguedad,
            "actual_polizas": polizas_tot,
            "actual_vida": polizas_vida,
            "actual_prima": prima,
            "meta_vida": meta["vida"],
            "meta_prima": meta["prima"],
            "cumple": cumple
        })
    
    return detalle

def obtener_detalle_alfa_2026(agentes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Determina qué agentes califican como ALFA según criterios de producción 2026.
    Criterios: >= 18 pólizas (ponderadas Vida) Y >= 700,000 en Prima neta Vida.
    """
    detalle = []
    for a in agentes_data:
        v_puntos = a.get("vida_puntos", 0)
        v_prima = a.get("vida_prima", 0)
        
        # Metas para ser ALFA (estándar AXA adaptado a ICP 2026)
        meta_polizas = 18
        meta_premium = 700000
        
        cumple = v_puntos >= meta_polizas and v_prima >= meta_premium
        
        detalle.append({
            "agente": a.get("nombre_completo"),
            "codigo": a.get("codigo_agente"),
            "vida_puntos": int(v_puntos),
            "vida_prima": float(v_prima),
            "meta_puntos": meta_polizas,
            "meta_prima": float(meta_premium),
            "cumple": cumple
        })
    return detalle
