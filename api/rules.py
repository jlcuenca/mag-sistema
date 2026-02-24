"""
Motor de reglas de negocio MAG-AXA
v0.2.0 — Actualizado con catálogo de 6 estatus reales y clasificación CY
"""
from datetime import date, datetime
import re

# ── Configuración ──────────────────────────────────────────────────
UMBRAL_COMISION_BASICA = 0.021   # 2.1% — configurable

# Catálogo de 6 estatus reales (fuente: EJEMPLO ESTATUS.xlsx)
CATALOGO_ESTATUS = {
    "PENDIENTE DE PAGO": "Póliza emitida dentro de los 30 días de fecha de emisión",
    "NO TOMADA":         "Póliza emitida no pagada dentro de los 30 días siguientes",
    "AL CORRIENTE":      "Póliza que tiene pagados las fracciones ya vencidas",
    "ATRASADA":          "Póliza dentro de los 30 días de un recibo diferente al 1er recibo",
    "CANCELADA":         "Póliza que no pagó dentro de los 30 días un recibo vencido",
    "REHABILITADA":      "Póliza pagada después de 31 días después de inicio de vigencia",
}

# Mapeo del estatus del cubo al estatus simplificado
ESTATUS_CUBO_MAP = {
    "POLIZA PAGADA":          "PAGADA",
    "POLIZA AL CORRIENTE":    "AL CORRIENTE",
    "POLIZA CANCELADA":       "CANCELADA",
    "POLIZA ATRASADA":        "ATRASADA",
    "POLIZA PENDIENTE":       "PENDIENTE DE PAGO",
    "POLIZA REHABILITADA":    "REHABILITADA",
    "POLIZA NO TOMADA":       "NO TOMADA",
}

# Segmentos con agrupamiento
SEGMENTOS = {
    "ALFA TOP INTEGRAL":  "ALFA",
    "ALFA TOP COMBINADO": "ALFA",
    "ALFA TOP":           "ALFA",
    "ALFA INTEGRAL":      "ALFA",
    "ALFA/BETA":          "ALFA",
    "BETA1":              "BETA",
    "BETA2":              "BETA",
    "OMEGA":              "OMEGA",
}


# ── REGLA 1 + 2: Clasificación Nueva / Subsecuente ─────────────────
def clasificar_poliza(
    ramo_codigo: int,
    fecha_inicio: str,
    status_recibo: str,
    anio_analisis: int,
    prima_neta: float = 0,
    comision: float = 0
) -> dict:
    """
    Clasifica una póliza como NUEVA, SUBSECUENTE o NO_APLICA
    aplicando las reglas de negocio del procedimiento MAG-AXA.
    """
    resultado = {
        "tipo_poliza": "NO_APLICA",
        "tipo_prima": None,
        "pct_comision": None,
        "es_nueva": False,
    }

    if not fecha_inicio:
        return resultado

    anio_poliza = int(fecha_inicio[:4])
    # Aceptar múltiples variantes de estatus como "pagada"
    pagada = status_recibo in ("PAGADA", "POLIZA PAGADA", "AL CORRIENTE", "POLIZA AL CORRIENTE")

    # ── GMM (ramo 34) ──
    if ramo_codigo == 34:
        if anio_poliza == anio_analisis and pagada:
            resultado.update({"tipo_poliza": "NUEVA", "es_nueva": True})
        elif anio_poliza == anio_analisis - 1:
            resultado.update({"tipo_poliza": "SUBSECUENTE", "es_nueva": False})

    # ── VIDA (ramo 11) ──
    elif ramo_codigo == 11:
        pct = (comision / prima_neta) if prima_neta and prima_neta > 0 else 0
        tipo_prima = "BASICA" if pct >= UMBRAL_COMISION_BASICA else "EXCEDENTE"
        resultado["tipo_prima"] = tipo_prima
        resultado["pct_comision"] = round(pct, 6)

        if tipo_prima == "BASICA":
            if anio_poliza == anio_analisis and pagada:
                resultado.update({"tipo_poliza": "NUEVA", "es_nueva": True})
            elif anio_poliza == anio_analisis - 1:
                resultado.update({"tipo_poliza": "SUBSECUENTE", "es_nueva": False})

    return resultado


# ── REGLA 3: Asegurado nuevo GMM ─────────────────────────────────
def es_asegurado_nuevo_gmm(
    pagada_en_periodo: bool,
    reconocimiento_antiguedad: bool,
    antiguedad_axa: str,
    fecha_inicio_vigencia: str
) -> bool:
    """
    Un asegurado GMM es nuevo si:
    1. Pagado en el periodo de análisis
    2. Sin reconocimiento de antigüedad AXA Individual
    3. Antigüedad AXA = fecha inicio de vigencia
    """
    if not pagada_en_periodo:
        return False
    if reconocimiento_antiguedad:
        return False
    if antiguedad_axa and fecha_inicio_vigencia:
        return antiguedad_axa[:10] == fecha_inicio_vigencia[:10]
    return False


# ── REGLA 4: Frontera de año ──────────────────────────────────────
def alerta_frontera_anio(fecha_pago: str) -> bool:
    """
    Detecta pagos del 2 al 5 de enero que pueden pertenecer al año anterior.
    """
    if not fecha_pago:
        return False
    try:
        d = datetime.fromisoformat(fecha_pago[:10])
        return d.month == 1 and 2 <= d.day <= 5
    except Exception:
        return False


# ── REGLA 5: Detección de reexpediciones ─────────────────────────
def es_reexpedicion(num_poliza: str) -> bool:
    """
    Una póliza reexpedida tiene terminación distinta a '00'.
    Ej: '0076384A00' → original, '0076384A01' → reexpedida
    """
    if not num_poliza:
        return False
    match = re.search(r'(\d{2})$', num_poliza.strip())
    if match:
        return int(match.group(1)) > 0
    return False


def extraer_raiz_poliza(num_poliza: str) -> str:
    """Extrae la raíz del número de póliza sin terminación de versión."""
    if not num_poliza:
        return num_poliza
    match = re.match(r'^(.+?)(\d{2})$', num_poliza.strip())
    return match.group(1) if match else num_poliza


# ── REGLA 6: MYSTATUS (actualizado con 6 estatus reales) ─────────
def calcular_mystatus(status_recibo: str, estatus_cubo: str = None, detalle: str = None) -> str:
    """
    Calcula el estado interno de una póliza.
    Ahora usa el catálogo de 6 estatus reales del Reporte Cubo.
    """
    # Si tenemos el estatus del cubo, usarlo directamente
    if estatus_cubo:
        mapped = ESTATUS_CUBO_MAP.get(estatus_cubo, "")
        if mapped == "CANCELADA" and detalle:
            if "FALTA DE PAGO" in detalle.upper():
                return "CANCELADA CADUCADA"
            elif "NO TOMADA" in detalle.upper():
                return "CANCELADA NO TOMADA"
            elif "SUSTITUCION" in detalle.upper():
                return "CANCELADA NO TOMADA"
            return "CANCELADA"
        return mapped

    # Fallback al mapeo original
    mapping = {
        "CANC/X F.PAGO": "CANCELADA CADUCADA",
        "CANC/X SUSTITUCION": "CANCELADA NO TOMADA",
        "PAGADA": "PAGADA TOTAL",
    }
    return mapping.get(status_recibo or "", "")


# ── REGLA 7: Normalización del número de póliza ──────────────────
def normalizar_poliza(num: str) -> str:
    """
    Normaliza el número de póliza eliminando ceros iniciales no significativos.
    Ej: '0076384A' → '76384A',  '00123U00' → '123U00'
    """
    if not num:
        return num
    # Quitar ceros iniciales antes del primer dígito significativo
    normalizado = re.sub(r'^0+(\d)', r'\1', str(num).strip())
    return normalizado


# ── Segmento agrupado ────────────────────────────────────────────
def agrupar_segmento(segmento: str) -> str:
    """Retorna el grupo del segmento (ALFA, BETA, OMEGA)."""
    if not segmento:
        return "OMEGA"  # default
    return SEGMENTOS.get(segmento.strip().upper(), "OMEGA")


# ── Mapeo de estatus del cubo ────────────────────────────────────
def mapear_estatus_cubo(estatus_cubo: str) -> str:
    """Convierte el estatus del cubo al estatus interno del sistema."""
    if not estatus_cubo:
        return ""
    return ESTATUS_CUBO_MAP.get(estatus_cubo.strip(), estatus_cubo)


# ── Clasificación CY ────────────────────────────────────────────
def clasificar_cy(clasificacion: str) -> dict:
    """
    Interpreta la clasificación CY del Reporte Cubo.
    'CY SUBSECUENTE' → subsecuente
    'CY ANUAL' → nueva del ciclo actual
    """
    if not clasificacion:
        return {"tipo_poliza": "NO_APLICA", "es_nueva": False}
    c = clasificacion.strip().upper()
    if "SUBSECUENTE" in c:
        return {"tipo_poliza": "SUBSECUENTE", "es_nueva": False}
    elif "ANUAL" in c:
        return {"tipo_poliza": "NUEVA", "es_nueva": True}
    return {"tipo_poliza": "NO_APLICA", "es_nueva": False}


# ── KPIs de dashboard ────────────────────────────────────────────
def calcular_kpis_polizas(polizas: list, anio: int) -> dict:
    """
    Calcula los KPIs principales a partir de una lista de dicts de pólizas.
    Optimizado con comprensiones de lista (más rápido que pandas para <50k reg).
    """
    del_anio = [p for p in polizas if p.get("anio_aplicacion") == anio]

    nuevas_vida = [
        p for p in del_anio
        if p.get("ramo_codigo") == 11
        and p.get("tipo_poliza") == "NUEVA"
        and p.get("tipo_prima") == "BASICA"
    ]
    nuevas_gmm = [
        p for p in del_anio
        if p.get("ramo_codigo") == 34
        and p.get("tipo_poliza") == "NUEVA"
    ]
    subs_vida = [
        p for p in del_anio
        if p.get("ramo_codigo") == 11
        and p.get("tipo_poliza") == "SUBSECUENTE"
    ]
    subs_gmm = [
        p for p in del_anio
        if p.get("ramo_codigo") == 34
        and p.get("tipo_poliza") == "SUBSECUENTE"
    ]

    return {
        "polizas_nuevas_vida": len(nuevas_vida),
        "prima_nueva_vida": sum(p.get("prima_neta") or 0 for p in nuevas_vida),
        "polizas_nuevas_gmm": len(nuevas_gmm),
        "asegurados_nuevos_gmm": sum(p.get("num_asegurados") or 1 for p in nuevas_gmm),
        "prima_nueva_gmm": sum(p.get("prima_neta") or 0 for p in nuevas_gmm),
        "prima_subsecuente_vida": sum(p.get("prima_neta") or 0 for p in subs_vida),
        "prima_subsecuente_gmm": sum(p.get("prima_neta") or 0 for p in subs_gmm),
        "canceladas_vida": sum(1 for p in del_anio if p.get("ramo_codigo") == 11 and p.get("mystatus") and "CANCELADA" in (p.get("mystatus") or "")),
        "canceladas_gmm": sum(1 for p in del_anio if p.get("ramo_codigo") == 34 and p.get("mystatus") and "CANCELADA" in (p.get("mystatus") or "")),
        "total_polizas": len(del_anio),
    }
