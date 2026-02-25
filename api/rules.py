"""
Motor de reglas de negocio MAG-AXA
v0.2.0 — Actualizado con catálogo de 6 estatus reales y clasificación CY
"""
from datetime import date, datetime
import re
import os

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


# ── REGLA 6: MYSTATUS (Motor Enriquecido — 6 estatus con lógica temporal) ─
def calcular_mystatus(
    status_recibo: str,
    estatus_cubo: str = None,
    detalle: str = None,
    fecha_emision: str = None,
    fecha_inicio: str = None,
    prima_pagada: float = None,
    prima_neta: float = None,
    es_primer_recibo: bool = True,
) -> str:
    """
    Motor de estatus enriquecido con lógica temporal de 30 días.

    Catálogo de 6 estatus (EJEMPLO ESTATUS.xlsx):
      1. PENDIENTE DE PAGO — Emitida, dentro de 30 días de emisión, sin pago
      2. NO TOMADA — Emitida, sin pago después de 30 días
      3. AL CORRIENTE — Fracciones vencidas pagadas
      4. ATRASADA — Dentro de 30 días de un recibo vencido (no el 1ro)
      5. CANCELADA — No se pagó dentro de 30 días un recibo vencido
      6. REHABILITADA — Pagada después de 31 días de inicio de vigencia
    """

    # ── 1. Si tenemos estatus del Reporte Cubo, usarlo como base ──
    if estatus_cubo:
        mapped = ESTATUS_CUBO_MAP.get(estatus_cubo, "")
        if mapped == "CANCELADA" and detalle:
            d = detalle.upper()
            if "FALTA DE PAGO" in d:
                return "CANCELADA CADUCADA"
            elif "NO TOMADA" in d:
                return "CANCELADA NO TOMADA"
            elif "SUSTITUCION" in d:
                return "CANCELADA POR SUSTITUCION"
            elif "REDUCCION" in d or "AUMENTO" in d:
                return "CANCELADA POR MODIFICACION"
            return "CANCELADA"
        if mapped == "REHABILITADA":
            return "REHABILITADA"
        if mapped:
            return mapped

    # ── 2. Lógica temporal basada en fechas ──
    hoy = date.today()

    if fecha_emision:
        try:
            f_emision = datetime.strptime(str(fecha_emision)[:10], "%Y-%m-%d").date()
            dias_desde_emision = (hoy - f_emision).days

            # Prima recibida vs esperada
            pagado = prima_pagada or 0
            esperado = prima_neta or 0

            if pagado <= 0:
                # Sin ningún pago
                if dias_desde_emision <= 30:
                    return "PENDIENTE DE PAGO"
                else:
                    return "NO TOMADA"

            if pagado >= esperado > 0:
                # Pagado completo — verificar si fue tardío
                if dias_desde_emision > 31 and es_primer_recibo:
                    return "REHABILITADA"
                return "PAGADA"

            if 0 < pagado < esperado:
                # Pago parcial
                if not es_primer_recibo:
                    return "ATRASADA"
                return "AL CORRIENTE"

        except (ValueError, TypeError):
            pass

    # ── 3. Lógica por fecha inicio (fallback) ──
    if fecha_inicio:
        try:
            f_inicio = datetime.strptime(str(fecha_inicio)[:10], "%Y-%m-%d").date()
            dias_desde_inicio = (hoy - f_inicio).days

            pagado = prima_pagada or 0
            if pagado <= 0 and dias_desde_inicio > 30:
                return "CANCELADA CADUCADA"
            elif pagado <= 0 and dias_desde_inicio <= 30:
                return "PENDIENTE DE PAGO"
        except (ValueError, TypeError):
            pass

    # ── 4. Fallback al mapeo original de status_recibo ──
    mapping = {
        "CANC/X F.PAGO": "CANCELADA CADUCADA",
        "CANC/X SUSTITUCION": "CANCELADA NO TOMADA",
        "CANC/NO TOMADA": "CANCELADA NO TOMADA",
        "PAGADA": "PAGADA",
        "AL CORRIENTE": "AL CORRIENTE",
        "ATRASADA": "ATRASADA",
        "PENDIENTE": "PENDIENTE DE PAGO",
        "REHABILITADA": "REHABILITADA",
    }
    sr = (status_recibo or "").strip().upper()
    for key, val in mapping.items():
        if key in sr:
            return val
    return ""


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


# ── REGLA 8: Cadena de renovaciones (Fase 3.1) ──────────────────
def construir_cadena_renovaciones(polizas: list) -> dict:
    """
    Construye la cadena Póliza Madre → Renovación Año X → Renovación Año Y.

    Recibe una lista de dicts con al menos: {poliza, raiz, version, anio, id}
    Retorna un dict de {poliza_id: poliza_madre_id} para actualizar la BD.

    Lógica: agrupa por raíz de póliza, ordena por año/versión, y enlaza
    cada póliza a su predecesora inmediata.
    """
    from collections import defaultdict

    # Agrupar por raíz
    grupos = defaultdict(list)
    for p in polizas:
        raiz = p.get("raiz") or extraer_raiz_poliza(p.get("poliza", ""))
        grupos[raiz].append(p)

    cadena = {}

    for raiz, pols in grupos.items():
        if len(pols) < 2:
            continue

        # Ordenar por año y luego por versión
        pols.sort(key=lambda x: (x.get("anio", 0) or 0, x.get("version", 0) or 0))

        # La primera es la madre, cada siguiente apunta a su predecesora
        for i in range(1, len(pols)):
            hijo_id = pols[i].get("id")
            madre_id = pols[i - 1].get("id")
            if hijo_id and madre_id:
                cadena[hijo_id] = madre_id

    return cadena


# ── REGLA 9: Cálculo de faltantes para metas (Fase 3.3) ──────────
def calcular_faltantes(
    meta_polizas: int = 0,
    meta_equiv: float = 0,
    meta_prima: float = 0,
    real_polizas: int = 0,
    real_equiv: float = 0,
    real_prima: float = 0,
) -> dict:
    """
    Calcula faltantes = meta - real.
    Si el real supera la meta, el faltante es 0 (ya se cumplió).
    """
    return {
        "faltante_polizas": max(0, (meta_polizas or 0) - (real_polizas or 0)),
        "faltante_equiv": max(0, (meta_equiv or 0) - (real_equiv or 0)),
        "faltante_prima": max(0, (meta_prima or 0) - (real_prima or 0)),
        "pct_cumplimiento": round(
            ((real_prima or 0) / meta_prima * 100) if meta_prima and meta_prima > 0 else 0, 1
        ),
    }


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


# ══════════════════════════════════════════════════════════════════
# REGLAS CALCULADAS — Columnas AUTOMATICO Excel (BE–CW)
# ══════════════════════════════════════════════════════════════════

# Tipo de cambio configurable (valores default del Excel)
TC_UDIS = float(os.environ.get("MAG_TC_UDIS", "8.56"))
TC_USD = float(os.environ.get("MAG_TC_USD", "18.38"))

# Meses en español para TEXT(fecha, "MMMM")
MESES_ES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
}

# Estatus que indican cancelación
ESTATUS_CANCELADA = {
    "CANCELADA NO TOMADA", "CANCELADA CADUCADA", "CANC/X F.PAGO",
    "CANC/X SUSTITUCION", "CANC/NO TOMADA", "CANC/A PETICION", "CANCELADA",
}


# ── BG: LARGO ────────────────────────────────────────────────────
def largo_poliza(num_poliza: str) -> int:
    """Largo del número de póliza. Excel: =LEN(AD2)"""
    return len(str(num_poliza).strip()) if num_poliza else 0


# ── BH: POLIZA CON 6 DE LARGO ───────────────────────────────────
def raiz_poliza_6(num_poliza: str) -> str:
    """Primeros 6 caracteres de la póliza. Excel: =LEFT(AD2,6)"""
    if not num_poliza:
        return ""
    return str(num_poliza).strip()[:6]


# ── BI: TERMINACIÓN ─────────────────────────────────────────────
def terminacion_poliza(num_poliza: str) -> str:
    """Últimos 2 caracteres del número de póliza. Excel: =RIGHT(AD2,2)"""
    if not num_poliza:
        return ""
    return str(num_poliza).strip()[-2:]


# ── BT: ID compuesto ────────────────────────────────────────────
def generar_id_compuesto(num_poliza: str, fecha_inicio: str) -> str:
    """
    Concatena póliza + fecha inicio como identificador único.
    Excel: =AD2&T2
    """
    pol = str(num_poliza).strip() if num_poliza else ""
    fec = str(fecha_inicio).strip() if fecha_inicio else ""
    return f"{pol}{fec}"


# ── BJ: PRIMER AÑO ──────────────────────────────────────────────
def determinar_primer_anio(
    num_poliza: str,
    fecha_inicio: str,
    anio_aplicacion: int,
    fecha_aplicacion: str = None,
    mystatus: str = None,
    fecperini: str = None,
    datos_fijos_primer_anio: str = None,
    poliza_en_indicadores: dict = None,
) -> str:
    """
    Determina si la póliza es de primer año y de qué periodo.
    Lógica del Excel:
    1. Si existe en DATOS FIJOS → usar valor de DATOS FIJOS
    2. Si existe en INDICADORES 2023/2024 → "PRIMER AÑO 20XX"
    3. Si fecha_aplicacion existe y año = 2025 → "PRIMER AÑO 2025"
    4. Si fecha_aplicacion existe y año = 2026 → "PRIMER AÑO 2026"
    5. Si año inicio = 2026 y no tiene FECPERINI → "PRIMER AÑO 2026, PENDIENTE DE PAGO"
    6. Sino → "-"
    """
    if not num_poliza:
        return "-"

    # Usar datos fijos si disponibles
    if datos_fijos_primer_anio and datos_fijos_primer_anio != "-":
        return datos_fijos_primer_anio

    # Usar indicadores históricos si disponibles
    if poliza_en_indicadores:
        for anio_ind in [2023, 2024, 2025]:
            if poliza_en_indicadores.get(anio_ind):
                return f"PRIMER AÑO {anio_ind}"

    # Inferir de fecha de aplicación
    if fecha_aplicacion and fecha_aplicacion != "-":
        try:
            anio_apli = int(fecha_aplicacion[:4])
            if anio_apli in (2023, 2024, 2025, 2026):
                return f"PRIMER AÑO {anio_apli}"
        except (ValueError, IndexError):
            pass

    # Inferir de anio_aplicacion
    if anio_aplicacion and anio_aplicacion >= 2023:
        if anio_aplicacion == 2026 and not fecperini:
            return "PRIMER AÑO 2026, PENDIENTE DE PAGO"
        return f"PRIMER AÑO {anio_aplicacion}"

    # Inferir de fecha de inicio de vigencia
    if fecha_inicio:
        try:
            anio_ini = int(fecha_inicio[:4])
            if anio_ini == 2026 and not fecperini:
                return "PRIMER AÑO 2026, PENDIENTE DE PAGO"
            if anio_ini >= 2023:
                return f"PRIMER AÑO {anio_ini}"
        except (ValueError, IndexError):
            pass

    return "-"


# ── BL: MES APLI ────────────────────────────────────────────────
def mes_aplicacion(fecha_aplicacion: str) -> str:
    """
    Nombre del mes en español a partir de la fecha de aplicación.
    Excel: =UPPER(TEXT(BK2,"MMMM"))
    """
    if not fecha_aplicacion or fecha_aplicacion == "-":
        return ""
    try:
        mes = int(fecha_aplicacion[5:7])
        return MESES_ES.get(mes, "")
    except (ValueError, IndexError):
        return ""


# ── BV: PENDIENTES DE PAGO ──────────────────────────────────────
def detectar_pendientes_pago(
    fecha_inicio: str,
    fecha_aplicacion: str,
    primer_anio: str,
    es_nueva: bool,
    ramo_codigo: int = None,
    fecha_emision: str = None,
) -> str:
    """
    Detecta pólizas pendientes de pago en 2026.
    Excel VIDA: =IF(T2<TODAY()-30,"",IF(BJ2="-",IF(AND(YEAR(T2)=2026,BE2=""),
                   "PRIMER AÑO 2026 PENDIENTE PAGO","-"),"-"))
    Excel GMM: =IF(OR(R2="VIEJA",...),"",...similar...)
    """
    if not fecha_inicio:
        return ""
    try:
        dt_inicio = datetime.strptime(fecha_inicio[:10], "%Y-%m-%d")
        hoy = datetime.now()

        # Si inicio es más de 30 días en el pasado, no aplica
        if (hoy - dt_inicio).days > 30:
            return ""

        if primer_anio == "-":
            anio_ini = dt_inicio.year
            if anio_ini == 2026 and (not fecha_aplicacion or fecha_aplicacion == "-"):
                return "PRIMER AÑO 2026 PENDIENTE PAGO"

        return "-"
    except Exception:
        return ""


# ── CA: TRIMESTRE ────────────────────────────────────────────────
def calcular_trimestre(fecha: str) -> str:
    """
    Calcula trimestre a partir de una fecha o nombre de mes.
    Retorna "Q1", "Q2", "Q3" o "Q4".
    """
    if not fecha or fecha == "-":
        return "-"
    try:
        if len(fecha) >= 7 and fecha[4] == "-":
            mes = int(fecha[5:7])
        else:
            # Intentar por nombre de mes
            mes_map = {v: k for k, v in MESES_ES.items()}
            mes = mes_map.get(fecha.strip().upper(), 0)
        if 1 <= mes <= 3:
            return "Q1"
        elif 4 <= mes <= 6:
            return "Q2"
        elif 7 <= mes <= 9:
            return "Q3"
        elif 10 <= mes <= 12:
            return "Q4"
    except (ValueError, IndexError):
        pass
    return "-"


# ── CI: PAGADA/NO PAGADA ────────────────────────────────────────
def flag_pagada(fecha_aplicacion: str) -> int:
    """
    1 si tiene fecha de aplicación (pagada), 0 si no.
    Excel: =IF(BU2="-",0,1)
    """
    if not fecha_aplicacion or fecha_aplicacion == "-" or fecha_aplicacion == "":
        return 0
    return 1


# ── CJ: NUEVA NO NUEVA FORM ─────────────────────────────────────
def flag_nueva_formal(
    anio_aplicacion: int,
    mystatus: str,
    prima_acumulada: float = 0,
    ramo_codigo: int = None,
) -> int:
    """
    Determina si la póliza cuenta como nueva formalmente.
    Excel VIDA: =IF(BM2=2025,IF(AM2=$DF$1,0,IF(AM2=$DF$2,0,1)),1)
      donde $DF$1="CANC/X F.PAGO", $DF$2="CANC/X SUSTITUCION"
    Excel GMM: =IF(BM2=2025,IF(OR(BD2="CANC/X SUSTITUCION",...,"CANCELADA"),0,
                  IF(BD2="",IF(CF2=0,0,1),1)),1)
    """
    current_year = datetime.now().year
    if anio_aplicacion != current_year and anio_aplicacion != current_year - 1:
        return 1

    ms = (mystatus or "").strip().upper()

    if ramo_codigo == 34:  # GMM — lógica más detallada
        if ms in ESTATUS_CANCELADA:
            return 0
        if ms == "" or ms is None:
            return 1 if prima_acumulada and prima_acumulada > 0 else 0
        return 1
    else:  # VIDA
        if ms in ("CANC/X F.PAGO", "CANC/X SUSTITUCION"):
            return 0
        return 1


# ── CM: PRIMA ANUAL EMITIDA EN PESOS ────────────────────────────
def prima_anual_en_pesos(prima_neta: float, moneda: str) -> float:
    """
    Convierte la prima neta a pesos mexicanos.
    Excel: =IF(Y2="UDIS",AF2*8.56,IF(Y2="USD",18.38*AF2,AF2))
    """
    if not prima_neta:
        return 0.0
    mon = (moneda or "MN").strip().upper()
    if mon == "UDIS" or mon == "UDI":
        return round(prima_neta * TC_UDIS, 2)
    elif mon == "USD" or mon == "DLS":
        return round(prima_neta * TC_USD, 2)
    return round(prima_neta, 2)


# ── CN: EQUIV (equivalencias emitidas) ──────────────────────────
def calcular_equivalencias(prima_anual_pesos: float, anio: int) -> float:
    """
    Calcula pólizas equivalentes emitidas según rangos de prima.
    Excel: =IF(T2="-",0,IF(YEAR(T2)=2024,
              IF(CM2=0,0,IF(CM2<15000,0.5,IF(CM2<50000,1,2))),
              IF(CM2=0,0,IF(CM2<16000,0.5,IF(CM2<50000,1,2)))))
    """
    if not prima_anual_pesos or prima_anual_pesos == 0:
        return 0.0
    umbral_bajo = 15000 if anio == 2024 else 16000
    if prima_anual_pesos < umbral_bajo:
        return 0.5
    elif prima_anual_pesos < 50000:
        return 1.0
    else:
        return 2.0


# ── CO: EQUIV PAGADA ────────────────────────────────────────────
def calcular_equivalencias_pagadas(
    prima_anual_pesos: float,
    prima_acumulada: float,
    anio: int,
    esta_cancelada: int,
    fecha_aplicacion: str = None,
) -> float:
    """
    Calcula pólizas equivalentes pagadas.
    Excel: =IF(CP2=0,0,IF(BU2="-",0,
              IF(YEAR(BU2)=2024,IF(CF2=0,0,IF(CM2<15000,0.5,IF(CM2<50000,1,2))),
              IF(CF2=0,0,IF(CM2<16000,0.5,IF(CM2<50000,1,2))))))
    """
    if esta_cancelada == 0:
        return 0.0
    if not fecha_aplicacion or fecha_aplicacion == "-":
        return 0.0
    if not prima_acumulada or prima_acumulada == 0:
        return 0.0
    return calcular_equivalencias(prima_anual_pesos, anio)


# ── CP: ESTA CANCELADA ──────────────────────────────────────────
def flag_cancelada(mystatus: str, prima_acumulada: float = 0) -> int:
    """
    0 si está cancelada, 1 si está vigente.
    Excel: =IF(OR(BD2="CANCELADA NO TOMADA",...),0,IF(BD2="",IF(CF2=0,0,1),1))
    """
    ms = (mystatus or "").strip().upper()
    if ms in ESTATUS_CANCELADA:
        return 0
    if ms == "":
        return 1 if prima_acumulada and prima_acumulada > 0 else 0
    return 1


# ── CU: Prima proporcional (días transcurridos) ─────────────────
def prima_proporcional(fecha_inicio: str, prima_neta: float, fecha_ref: str = None) -> float:
    """
    Prima proporcional al tiempo transcurrido desde inicio de vigencia.
    Excel VIDA: =(($DB$1-T2)/(365))*CM2  (donde $DB$1 = TODAY()-28)
    Excel GMM:  =(($CV$1-T2)/(365))*AF2  (donde $CV$1 = TODAY()-30)
    """
    if not fecha_inicio or not prima_neta:
        return 0.0
    try:
        dt_inicio = datetime.strptime(fecha_inicio[:10], "%Y-%m-%d")
        if fecha_ref:
            dt_ref = datetime.strptime(fecha_ref[:10], "%Y-%m-%d")
        else:
            dt_ref = datetime.now()
            dt_ref = dt_ref.replace(hour=0, minute=0, second=0, microsecond=0)
            # Usar TODAY()-28 como el Excel (aproximación)
            from datetime import timedelta
            dt_ref = dt_ref - timedelta(days=28)
        dias = (dt_ref - dt_inicio).days
        if dias <= 0:
            return 0.0
        return round((dias / 365.0) * prima_neta, 2)
    except Exception:
        return 0.0


# ── CV/CN: CONDICIONAL PRIMA ────────────────────────────────────
def condicional_prima(prima_acumulada: float, prima_prop: float) -> str:
    """
    Valida si la prima acumulada es suficiente vs. la prima proporcional.
    Excel: =IF(CF2<CU2,"Cancelada","OK")
    """
    if prima_acumulada is None or prima_prop is None:
        return ""
    if prima_acumulada < prima_prop:
        return "Cancelada"
    return "OK"


# ══════════════════════════════════════════════════════════════════
# ORQUESTADOR: Aplica todas las reglas a una póliza
# ══════════════════════════════════════════════════════════════════

def aplicar_reglas_poliza(poliza: dict, ramo_codigo: int = None) -> dict:
    """
    Aplica todas las reglas de cálculo a un dict de póliza.
    Retorna un dict con los campos calculados.

    Args:
        poliza: dict con campos raw de la póliza
        ramo_codigo: 11 (Vida) o 34 (GMM)

    Returns:
        dict con los campos calculados para actualizar la póliza
    """
    pol_num = str(poliza.get("poliza_original") or "").strip()
    fecha_ini = poliza.get("fecha_inicio") or ""
    prima_neta = poliza.get("prima_neta") or 0
    moneda = poliza.get("moneda") or "MN"
    ms = poliza.get("mystatus") or ""
    status = poliza.get("status_recibo") or ""
    anio = poliza.get("anio_aplicacion") or datetime.now().year
    fecha_apli = poliza.get("fecha_aplicacion") or poliza.get("fecha_primer_pago") or ""
    nueva_flag = poliza.get("es_nueva")

    # Campos simples de texto
    _largo = largo_poliza(pol_num)
    _raiz6 = raiz_poliza_6(pol_num)
    _terminacion = terminacion_poliza(pol_num)
    _id_comp = generar_id_compuesto(pol_num, fecha_ini)
    _reexp = es_reexpedicion(pol_num)

    # Fecha de aplicación y derivados
    if not fecha_apli or fecha_apli == "-":
        # Si tiene status PAGADA, inferir de fecha_inicio
        if status in ("PAGADA", "AL CORRIENTE", "POLIZA PAGADA", "POLIZA AL CORRIENTE"):
            fecha_apli = fecha_ini
    _mes_apli = mes_aplicacion(fecha_apli)
    _anio_apli = None
    if fecha_apli and fecha_apli != "-" and len(fecha_apli) >= 4:
        try:
            _anio_apli = int(fecha_apli[:4])
        except ValueError:
            pass

    # Primer año
    _primer_anio = determinar_primer_anio(
        num_poliza=pol_num,
        fecha_inicio=fecha_ini,
        anio_aplicacion=_anio_apli or anio,
        fecha_aplicacion=fecha_apli,
        mystatus=ms,
    )

    # Pendientes de pago
    _pendientes = detectar_pendientes_pago(
        fecha_inicio=fecha_ini,
        fecha_aplicacion=fecha_apli,
        primer_anio=_primer_anio,
        es_nueva=nueva_flag,
        ramo_codigo=ramo_codigo,
    )

    # Trimestre
    _trimestre = calcular_trimestre(fecha_apli)

    # Flag pagada
    _flag_pag = flag_pagada(fecha_apli)

    # Prima en pesos
    _prima_pesos = prima_anual_en_pesos(prima_neta, moneda)

    # Prima acumulada (usar valor existente si hay, sino prima neta si pagada)
    _prima_acum = poliza.get("prima_acumulada_basica") or poliza.get("neta_acumulada") or 0
    if _flag_pag and not _prima_acum:
        _prima_acum = _prima_pesos

    # Flag cancelada
    _flag_canc = flag_cancelada(ms, _prima_acum)

    # Nueva formal
    _flag_nueva = flag_nueva_formal(
        anio_aplicacion=anio,
        mystatus=ms,
        prima_acumulada=_prima_acum,
        ramo_codigo=ramo_codigo,
    )

    # Equivalencias emitidas
    _equiv = calcular_equivalencias(_prima_pesos, anio)

    # Equivalencias pagadas
    _equiv_pag = calcular_equivalencias_pagadas(
        prima_anual_pesos=_prima_pesos,
        prima_acumulada=_prima_acum,
        anio=anio,
        esta_cancelada=_flag_canc,
        fecha_aplicacion=fecha_apli,
    )

    # Prima proporcional
    _prima_prop = prima_proporcional(fecha_ini, _prima_pesos)

    # Condicional de prima
    _cond_prima = condicional_prima(_prima_acum, _prima_prop)

    return {
        "largo_poliza": _largo,
        "raiz_poliza_6": _raiz6,
        "terminacion": _terminacion,
        "id_compuesto": _id_comp,
        "es_reexpedicion": _reexp,
        "primer_anio": _primer_anio,
        "fecha_aplicacion": fecha_apli if fecha_apli and fecha_apli != "-" else None,
        "mes_aplicacion": _mes_apli,
        "pendientes_pago": _pendientes,
        "trimestre": _trimestre,
        "flag_pagada": _flag_pag,
        "flag_nueva_formal": _flag_nueva,
        "prima_anual_pesos": _prima_pesos,
        "prima_acumulada_basica": _prima_acum if _prima_acum else None,
        "equivalencias_emitidas": _equiv,
        "equivalencias_pagadas": _equiv_pag,
        "flag_cancelada": _flag_canc,
        "prima_proporcional": _prima_prop,
        "condicional_prima": _cond_prima,
    }


def aplicar_reglas_batch(polizas: list, ramo_codigo: int = None) -> list:
    """
    Aplica las reglas a un lote de pólizas y calcula los campos que
    dependen del conjunto completo (num_reexpediciones).

    Args:
        polizas: lista de dicts con campos raw de pólizas
        ramo_codigo: 11 (Vida) o 34 (GMM), None si mixto

    Returns:
        lista de dicts con los campos calculados por póliza
    """
    # Paso 1: Calcular campos individuales
    resultados = []
    for p in polizas:
        rc = ramo_codigo
        if rc is None:
            ramo_raw = (p.get("ramo_nombre_raw") or p.get("ramo_nombre") or "").upper()
            if "VIDA" in ramo_raw:
                rc = 11
            elif "GASTO" in ramo_raw or "GMM" in ramo_raw:
                rc = 34
        campos = aplicar_reglas_poliza(p, ramo_codigo=rc)
        resultados.append(campos)

    # Paso 2: Contar reexpediciones (BF: COUNTIF sobre raíz de 6 chars)
    from collections import Counter
    raices = Counter(r["raiz_poliza_6"] for r in resultados if r["raiz_poliza_6"])
    for r in resultados:
        raiz = r["raiz_poliza_6"]
        r["num_reexpediciones"] = raices.get(raiz, 0) if raiz else 0

    return resultados
