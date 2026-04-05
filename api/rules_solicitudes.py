"""
Motor de reglas de negocio para SOLICITUDES — MAG-AXA
=====================================================
Reglas S1–S5 para la entidad raíz del sistema.
Toda solicitud se registra y procesa; puede convertirse en póliza.

Refactor v2.0 — Solicitud-Céntrico
"""
from datetime import datetime, date


# ══════════════════════════════════════════════════════════════════
# REGLA S1: Normalización de Ramo
# ══════════════════════════════════════════════════════════════════

RAMO_MAP = {
    "SALUD": "GMM",
    "GASTOS MEDICOS": "GMM",
    "GASTOS MEDICOS MAYORES": "GMM",
    "GASTOS MEDICOS MAYORES INDIVIDUAL": "GMM",
    "GMM": "GMM",
    "VIDA": "VIDA",
    "VIDA INDIVIDUAL": "VIDA",
    "GAMMA FLEX IND.": "VIDA",
}


def normalizar_ramo(nomramo: str) -> str:
    """
    S1: Normaliza el nombre del ramo a 'VIDA' o 'GMM'.
    Maneja todas las variantes usadas en los diferentes CSVs y hojas Excel.
    """
    if not nomramo:
        return ""
    upper = nomramo.strip().upper()
    # Búsqueda directa
    if upper in RAMO_MAP:
        return RAMO_MAP[upper]
    # Búsqueda parcial
    if "SALUD" in upper or "GMM" in upper or "GASTOS" in upper or "FLEX" in upper:
        return "GMM"
    if "VIDA" in upper or "GAMMA" in upper:
        return "VIDA"
    return upper  # fallback: devolver tal cual


# ══════════════════════════════════════════════════════════════════
# REGLA S2: Estado derivado de Etapa
# ══════════════════════════════════════════════════════════════════

# Etapas AXA conocidas y su mapeo a estado interno
ETAPA_ESTADO_MAP = {
    # Exitosas → EMITIDA
    "POLIZA_ENVIADA": "EMITIDA",
    "EMISION": "EMITIDA",

    # Rechazos → RECHAZADA
    "RECHAZO_EMISION": "RECHAZADA",
    "RECHAZO_EXPIRACION": "RECHAZADA",
    "RECHAZO_SELECCION": "RECHAZADA",
    "RECHAZO_AUT_INFO_AD": "RECHAZADA",

    # Cancelación → CANCELADA
    "CANCELADO": "CANCELADA",
    "CANCELADA": "CANCELADA",

    # En proceso → TRAMITE
    "LIBERACION_EMISION": "TRAMITE",
    "LIBERACION_SELECCION": "TRAMITE",
    "INFO_AD_EMISION": "TRAMITE",
    "INFO_AD_SELECCION": "TRAMITE",
    "SELECCION": "TRAMITE",
}

# Mapeo de tipo de rechazo
TIPO_RECHAZO_MAP = {
    "RECHAZO_EMISION": "RECHAZO EN EMISIÓN",
    "RECHAZO_EXPIRACION": "RECHAZO POR EXPIRACIÓN",
    "RECHAZO_SELECCION": "RECHAZO EN SELECCIÓN",
    "RECHAZO_AUT_INFO_AD": "RECHAZO POR INFO ADICIONAL",
}


def derivar_estado_de_etapa(
    etapa: str,
    poliza_numero: str = None,
) -> dict:
    """
    S2: Deriva el estado de la solicitud a partir de la etapa AXA.

    Returns:
        dict con: estado, tipo_rechazo
    """
    resultado = {
        "estado": "TRAMITE",
        "tipo_rechazo": None,
    }

    if not etapa:
        return resultado

    etapa_upper = etapa.strip().upper()

    # Buscar en mapa
    estado = ETAPA_ESTADO_MAP.get(etapa_upper)
    if estado:
        resultado["estado"] = estado

    # Si es emisión/póliza enviada y hay póliza, confirmar EMITIDA
    if estado == "EMITIDA" and poliza_numero:
        pol = str(poliza_numero).strip().upper()
        if pol and pol != "PENDIENTE" and pol != "":
            resultado["estado"] = "EMITIDA"
        else:
            resultado["estado"] = "TRAMITE"  # Tiene etapa pero no póliza todavía

    # Tipo de rechazo
    if estado == "RECHAZADA":
        resultado["tipo_rechazo"] = TIPO_RECHAZO_MAP.get(etapa_upper, "RECHAZO GENÉRICO")

    return resultado


# ══════════════════════════════════════════════════════════════════
# REGLA S3: Vinculación Solicitud ↔ Póliza
# ══════════════════════════════════════════════════════════════════

def puede_vincular_poliza(poliza_numero: str) -> bool:
    """
    S3: Determina si la solicitud puede vincularse a una póliza.
    Retorna True si el campo poliza tiene un valor válido (no PENDIENTE, no vacío).
    """
    if not poliza_numero:
        return False
    pol = str(poliza_numero).strip().upper()
    return pol not in ("", "PENDIENTE", "-", "0", "NONE", "NAN", "NULL")


def normalizar_poliza_para_cruce(poliza_numero: str) -> str:
    """
    Normaliza el número de póliza de la solicitud para cruzar con la tabla polizas.
    Reutiliza la lógica de api/rules.py pero adaptada.
    """
    import re
    if not poliza_numero:
        return ""
    pol = str(poliza_numero).strip()
    # Quitar ceros iniciales
    normalizado = re.sub(r'^0+(\d)', r'\1', pol)
    return normalizado


# ══════════════════════════════════════════════════════════════════
# REGLA S4: Alerta de solicitud atorada
# ══════════════════════════════════════════════════════════════════

UMBRAL_DIAS_ATORADA = 15  # Configurable


def detectar_solicitud_atorada(
    fecha_ultima_etapa: str,
    estado: str = "TRAMITE",
    fecha_referencia: str = None,
) -> int:
    """
    S4: Detecta solicitudes que llevan más de N días sin movimiento.

    Args:
        fecha_ultima_etapa: Fecha de la última etapa registrada
        estado: Estado actual de la solicitud
        fecha_referencia: Fecha de comparación (default: hoy)

    Returns:
        1 si está atorada, 0 si no
    """
    # Solo aplica a solicitudes en trámite
    if estado and estado.upper() not in ("TRAMITE",):
        return 0

    if not fecha_ultima_etapa:
        return 0

    try:
        f_etapa = datetime.strptime(str(fecha_ultima_etapa)[:10], "%Y-%m-%d").date()
        if fecha_referencia:
            f_ref = datetime.strptime(str(fecha_referencia)[:10], "%Y-%m-%d").date()
        else:
            f_ref = date.today()

        dias = (f_ref - f_etapa).days
        return 1 if dias > UMBRAL_DIAS_ATORADA else 0
    except (ValueError, TypeError):
        return 0


# ══════════════════════════════════════════════════════════════════
# REGLA S5: Tasa de conversión por agente
# ══════════════════════════════════════════════════════════════════

def calcular_tasa_conversion(
    total_solicitudes: int,
    solicitudes_emitidas: int,
) -> float:
    """
    S5: Calcula la tasa de conversión de solicitud a póliza.
    tasa = emitidas / total × 100

    Se calcula en batch por agente.
    """
    if not total_solicitudes or total_solicitudes == 0:
        return 0.0
    return round((solicitudes_emitidas / total_solicitudes) * 100, 1)


# ══════════════════════════════════════════════════════════════════
# REGLA S6: Cálculo de días de trámite
# ══════════════════════════════════════════════════════════════════

def calcular_dias_tramite(fecrecepcion: str, fecetapa: str) -> int:
    """
    Calcula los días transcurridos entre recepción y la etapa.
    """
    if not fecrecepcion or not fecetapa:
        return None
    try:
        d1 = datetime.strptime(str(fecrecepcion)[:10], "%Y-%m-%d").date()
        d2 = datetime.strptime(str(fecetapa)[:10], "%Y-%m-%d").date()
        return (d2 - d1).days
    except (ValueError, TypeError):
        return None


# ══════════════════════════════════════════════════════════════════
# REGLA S7: SLA cumplido
# ══════════════════════════════════════════════════════════════════

SLA_DIAS_MAX = 30  # SLA estándar AXA: 30 días


def evaluar_sla(dias_tramite: int) -> int:
    """
    Evalúa si el trámite se completó dentro del SLA de AXA.

    Returns:
        1 si cumple SLA, 0 si no, None si no hay datos
    """
    if dias_tramite is None:
        return None
    return 1 if dias_tramite <= SLA_DIAS_MAX else 0


# ══════════════════════════════════════════════════════════════════
# ORQUESTADOR: Aplica todas las reglas a una solicitud
# ══════════════════════════════════════════════════════════════════

def aplicar_reglas_solicitud(solicitud: dict) -> dict:
    """
    Aplica las reglas S1–S7 a un dict de solicitud.

    Args:
        solicitud: dict con campos crudos de la solicitud

    Returns:
        dict con los campos calculados para UPDATE
    """
    nomramo = solicitud.get("nomramo") or solicitud.get("ramo") or ""
    etapa = solicitud.get("ultima_etapa") or solicitud.get("etapa") or ""
    poliza = solicitud.get("poliza_numero") or solicitud.get("poliza") or ""
    fecrecepcion = solicitud.get("fecrecepcion") or ""
    fecetapa = solicitud.get("fecha_ultima_etapa") or solicitud.get("fecetapa") or ""

    # S1: Normalizar ramo
    ramo_norm = normalizar_ramo(nomramo)

    # S2: Derivar estado
    estado_result = derivar_estado_de_etapa(etapa, poliza)

    # S3: ¿Puede vincular póliza?
    vinculable = puede_vincular_poliza(poliza)
    poliza_normalizada = normalizar_poliza_para_cruce(poliza) if vinculable else None

    # S6: Días de trámite
    dias = calcular_dias_tramite(fecrecepcion, fecetapa)

    # S4: Alerta atorada
    alerta = detectar_solicitud_atorada(fecetapa, estado_result["estado"])

    # S7: SLA
    sla = evaluar_sla(dias)

    return {
        "ramo_normalizado": ramo_norm,
        "estado": estado_result["estado"],
        "tipo_rechazo": estado_result["tipo_rechazo"],
        "dias_tramite": dias,
        "alerta_atorada": alerta,
        "sla_cumplido": sla,
        "poliza_numero_normalizada": poliza_normalizada,
        "puede_vincular": vinculable,
    }


def aplicar_reglas_solicitudes_batch(solicitudes: list) -> list:
    """
    Aplica las reglas a un lote de solicitudes.

    Args:
        solicitudes: lista de dicts con campos de solicitud

    Returns:
        lista de dicts con campos calculados (incluye 'id' para UPDATE)
    """
    resultados = []
    for sol in solicitudes:
        result = aplicar_reglas_solicitud(sol)
        result["id"] = sol.get("id")
        resultados.append(result)
    return resultados


# ══════════════════════════════════════════════════════════════════
# KPIs de Pipeline
# ══════════════════════════════════════════════════════════════════

def calcular_kpis_pipeline(solicitudes: list, anio: int = None) -> dict:
    """
    Calcula KPIs del pipeline de solicitudes.

    Args:
        solicitudes: lista de dicts de solicitudes
        anio: año para filtrar (None = todas)

    Returns:
        dict con KPIs del pipeline
    """
    if anio:
        filtradas = [s for s in solicitudes if s.get("ano_recepcion") == anio]
    else:
        filtradas = solicitudes

    total = len(filtradas)
    en_tramite = sum(1 for s in filtradas if s.get("estado") == "TRAMITE")
    emitidas = sum(1 for s in filtradas if s.get("estado") == "EMITIDA")
    rechazadas = sum(1 for s in filtradas if s.get("estado") == "RECHAZADA")
    canceladas = sum(1 for s in filtradas if s.get("estado") == "CANCELADA")
    pagadas = sum(1 for s in filtradas if s.get("estado") == "PAGADA")
    atoradas = sum(1 for s in filtradas if s.get("alerta_atorada") == 1)

    # Tasa de conversión global
    tasa = calcular_tasa_conversion(total, emitidas + pagadas)

    # Días promedio de trámite
    dias_list = [s.get("dias_tramite") for s in filtradas
                 if s.get("dias_tramite") is not None and s.get("dias_tramite") >= 0]
    dias_promedio = round(sum(dias_list) / len(dias_list), 1) if dias_list else 0

    # SLA
    sla_list = [s.get("sla_cumplido") for s in filtradas
                if s.get("sla_cumplido") is not None]
    pct_sla = round(sum(s for s in sla_list if s == 1) / len(sla_list) * 100, 1) if sla_list else 0

    # Por ramo
    vida = sum(1 for s in filtradas if s.get("ramo_normalizado") == "VIDA")
    gmm = sum(1 for s in filtradas if s.get("ramo_normalizado") == "GMM")

    return {
        "total": total,
        "en_tramite": en_tramite,
        "emitidas": emitidas,
        "rechazadas": rechazadas,
        "canceladas": canceladas,
        "pagadas": pagadas,
        "atoradas": atoradas,
        "tasa_conversion": tasa,
        "dias_promedio_tramite": dias_promedio,
        "pct_sla_cumplido": pct_sla,
        "por_ramo": {"vida": vida, "gmm": gmm},
        "funnel": {
            "ingresadas": total,
            "en_proceso": en_tramite,
            "emitidas": emitidas,
            "pagadas": pagadas,
            "rechazadas": rechazadas,
            "canceladas": canceladas,
        },
    }
