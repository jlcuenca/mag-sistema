"""
Schemas Pydantic para validación y serialización de la API MAG
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


# ── Agentes ───────────────────────────────────────────────────────
class AgenteBase(BaseModel):
    codigo_agente: str
    nombre_completo: str
    rol: Optional[str] = "Agente"
    situacion: Optional[str] = "ACTIVO"
    fecha_alta: Optional[str] = None
    fecha_cancelacion: Optional[str] = None
    territorio: Optional[str] = None
    oficina: Optional[str] = None
    gerencia: Optional[str] = None
    promotor: Optional[str] = None
    centro_costos: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None


class AgenteCreate(AgenteBase):
    pass


class AgenteOut(AgenteBase):
    id: int
    total_polizas: Optional[int] = 0
    polizas_nuevas_2025: Optional[int] = 0
    prima_nueva_2025: Optional[float] = 0.0

    model_config = {"from_attributes": True}


# ── Pólizas ───────────────────────────────────────────────────────
class PolizaBase(BaseModel):
    poliza_original: str
    agente_id: Optional[int] = None
    producto_id: Optional[int] = None
    asegurado_nombre: Optional[str] = None
    rfc: Optional[str] = None
    fecha_inicio: str
    fecha_fin: Optional[str] = None
    moneda: Optional[str] = "MN"
    prima_total: Optional[float] = None
    prima_neta: Optional[float] = None
    iva: Optional[float] = 0
    recargo: Optional[float] = 0
    suma_asegurada: Optional[float] = None
    deducible: Optional[float] = None
    coaseguro: Optional[float] = None
    num_asegurados: Optional[int] = 1
    forma_pago: Optional[str] = None
    tipo_pago: Optional[str] = None
    status_recibo: Optional[str] = "PAGADA"
    gama: Optional[str] = None
    tipo_poliza: Optional[str] = None
    tipo_prima: Optional[str] = None
    notas: Optional[str] = None


class PolizaCreate(PolizaBase):
    pass


class PolizaOut(PolizaBase):
    id: int
    poliza_estandar: Optional[str] = None
    es_nueva: Optional[bool] = None
    mystatus: Optional[str] = None
    periodo_aplicacion: Optional[str] = None
    anio_aplicacion: Optional[int] = None
    fuente: Optional[str] = None
    # Campos de joins
    agente_nombre: Optional[str] = None
    codigo_agente: Optional[str] = None
    oficina: Optional[str] = None
    gerencia: Optional[str] = None
    territorio: Optional[str] = None
    ramo_codigo: Optional[int] = None
    ramo_nombre: Optional[str] = None
    plan: Optional[str] = None
    # Campos nuevos del Reporte Cubo
    segmento: Optional[str] = None
    gestion_comercial: Optional[str] = None
    clasificacion_cy: Optional[str] = None
    estatus_cubo: Optional[str] = None
    estatus_detalle: Optional[str] = None
    contratante_nombre: Optional[str] = None
    neta_total_contrato: Optional[float] = None
    neta_acumulada: Optional[float] = None
    neta_forma_pago: Optional[float] = None

    model_config = {"from_attributes": True}


class PolizaListResponse(BaseModel):
    data: List[PolizaOut]
    total: int
    page: int
    limit: int
    pages: int


# ── Dashboard ─────────────────────────────────────────────────────
class KPIs(BaseModel):
    polizas_nuevas_vida: int = 0
    prima_nueva_vida: float = 0
    polizas_nuevas_gmm: int = 0
    asegurados_nuevos_gmm: int = 0
    prima_nueva_gmm: float = 0
    prima_subsecuente_vida: float = 0
    prima_subsecuente_gmm: float = 0
    polizas_canceladas: int = 0
    total_polizas: int = 0
    meta_vida: int = 0
    meta_gmm: int = 0
    meta_prima_vida: float = 0
    meta_prima_gmm: float = 0


class ProduccionMensual(BaseModel):
    periodo: str
    polizas_vida: int = 0
    polizas_gmm: int = 0
    prima_vida: float = 0
    prima_gmm: float = 0


class TopAgente(BaseModel):
    nombre_completo: Optional[str] = None
    codigo_agente: Optional[str] = None
    oficina: Optional[str] = None
    segmento: Optional[str] = None
    polizas_nuevas: int = 0
    prima_total: float = 0


class DistribucionGama(BaseModel):
    gama: Optional[str] = None
    total: int = 0
    prima: float = 0


class DashboardResponse(BaseModel):
    kpis: KPIs
    produccion_mensual: List[ProduccionMensual]
    top_agentes: List[TopAgente]
    distribucion_gama: List[DistribucionGama]


# ── Dashboard Ejecutivo (Fase 1) ──────────────────────────────────
class ComparativoRamo(BaseModel):
    """Comparativo interanual por ramo (replica VISTAS.xlsx)"""
    ramo: str  # 'GMM' o 'VIDA'
    polizas_anterior: int = 0
    polizas_actual: int = 0
    polizas_variacion: float = 0
    asegurados_anterior: int = 0
    asegurados_actual: int = 0
    asegurados_variacion: float = 0
    equivalentes_anterior: float = 0  # Solo Vida
    equivalentes_actual: float = 0
    equivalentes_variacion: float = 0
    prima_nueva_anterior: float = 0
    prima_nueva_actual: float = 0
    prima_nueva_variacion: float = 0
    prima_subsecuente_anterior: float = 0
    prima_subsecuente_actual: float = 0
    prima_subsecuente_variacion: float = 0
    prima_total_anterior: float = 0
    prima_total_actual: float = 0
    prima_total_variacion: float = 0


class ResumenSegmento(BaseModel):
    """Resumen por segmento ALFA/BETA/OMEGA"""
    segmento: str
    num_agentes: int = 0
    polizas_vida: int = 0
    polizas_gmm: int = 0
    prima_vida: float = 0
    prima_gmm: float = 0
    prima_total: float = 0
    equivalentes: float = 0


class AgenteOperativo(BaseModel):
    """Vista operativa por agente (47 columnas de VISTAS CUITLAHUAC)"""
    clave: Optional[str] = None
    nombre: Optional[str] = None
    segmento: Optional[str] = None
    segmento_agrupado: Optional[str] = None
    gestion: Optional[str] = None
    estado: Optional[str] = None
    # Vida actual
    polizas_vida: int = 0
    equiv_vida: float = 0
    prima_pagada_vida: float = 0
    # GMM actual
    polizas_gmm: int = 0
    asegurados_gmm: int = 0
    prima_pagada_gmm: float = 0
    # Total
    prima_pagada_total: float = 0
    # Metas
    meta_polizas: int = 0
    meta_equiv: float = 0
    faltante_polizas: int = 0
    meta_prima_vida: float = 0
    falta_prima_vida: float = 0
    meta_prima_gmm: float = 0
    falta_prima_gmm: float = 0
    # Comparativo GMM
    gmm_polizas_ant: int = 0
    gmm_polizas_act: int = 0
    gmm_prima_nueva_ant: float = 0
    gmm_prima_nueva_act: float = 0
    gmm_prima_sub_ant: float = 0
    gmm_prima_sub_act: float = 0
    gmm_total_ant: float = 0
    gmm_total_act: float = 0
    gmm_crecimiento: float = 0
    # Comparativo Vida
    vida_polizas_ant: int = 0
    vida_polizas_act: int = 0
    vida_equiv_ant: float = 0
    vida_equiv_act: float = 0
    vida_prima_nueva_ant: float = 0
    vida_prima_nueva_act: float = 0
    vida_prima_sub_ant: float = 0
    vida_prima_sub_act: float = 0
    vida_total_ant: float = 0
    vida_total_act: float = 0
    vida_crecimiento: float = 0


class ProduccionMensualComparativo(BaseModel):
    """Producción mensual con comparación interanual."""
    mes: str  # 'Ene', 'Feb', etc.
    mes_num: int
    polizas_anterior: int = 0
    polizas_actual: int = 0
    prima_anterior: float = 0
    prima_actual: float = 0


class EjecutivoResponse(BaseModel):
    comparativo_gmm: ComparativoRamo
    comparativo_vida: ComparativoRamo
    segmentos: List[ResumenSegmento]
    agentes_operativo: List[AgenteOperativo]
    mensual_gmm: List[ProduccionMensualComparativo]
    mensual_vida: List[ProduccionMensualComparativo]
    anio_actual: int
    anio_anterior: int
    filtros_disponibles: dict = {}


# ── Cobranza / Deudor (Fase 2) ────────────────────────────────────
class DeudorPrima(BaseModel):
    """Vista Deudor por Prima — una fila por póliza con semáforo de urgencia."""
    poliza: str
    contratante: Optional[str] = None
    asegurado: Optional[str] = None
    agente_clave: Optional[str] = None
    agente_nombre: Optional[str] = None
    ramo: Optional[str] = None
    plan: Optional[str] = None
    gama: Optional[str] = None
    segmento: Optional[str] = None
    prima_neta: float = 0
    prima_total: float = 0
    prima_acumulada: float = 0
    prima_pendiente: float = 0
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    fecha_proximo_recibo: Optional[str] = None
    status: Optional[str] = None
    mystatus: Optional[str] = None
    dias_vencimiento: int = 0
    # Semáforo: 'critico' / 'urgente' / 'atencion' / 'al_dia' / 'pagado'
    prioridad: str = 'al_dia'
    recibo_actual: Optional[str] = None  # 'n/m' (e.g. 3/12)
    moneda: Optional[str] = 'MN'


class CobranzaResumen(BaseModel):
    """KPIs de cobranza"""
    total_polizas: int = 0
    criticas: int = 0
    urgentes: int = 0
    atencion: int = 0
    al_dia: int = 0
    pagadas: int = 0
    prima_por_cobrar: float = 0
    prima_cobrada: float = 0
    pct_cobranza: float = 0


class RenovacionPendiente(BaseModel):
    """Póliza próxima a renovar"""
    poliza: str
    contratante: Optional[str] = None
    agente_nombre: Optional[str] = None
    agente_clave: Optional[str] = None
    ramo: Optional[str] = None
    prima_neta: float = 0
    fecha_fin: Optional[str] = None
    dias_para_renovar: int = 0
    status: Optional[str] = None
    # 'por_vencer' / 'vencida' / 'renovada'
    estado_renovacion: str = 'por_vencer'


class PolizaCancelada(BaseModel):
    """Detalle de póliza cancelada"""
    poliza: str
    contratante: Optional[str] = None
    agente_nombre: Optional[str] = None
    agente_clave: Optional[str] = None
    ramo: Optional[str] = None
    prima_neta: float = 0
    prima_acumulada: float = 0
    prima_perdida: float = 0
    fecha_inicio: Optional[str] = None
    mystatus: Optional[str] = None
    motivo: Optional[str] = None
    estatus_detalle: Optional[str] = None


class AlertaCobranza(BaseModel):
    """Alerta de cobranza"""
    tipo: str  # 'vencido', 'por_cancelar', 'pendiente', 'renovacion'
    icono: str = '⚠️'
    titulo: str
    descripcion: str
    poliza: Optional[str] = None
    agente: Optional[str] = None
    dias: int = 0
    monto: float = 0


class SeguimientoMensual(BaseModel):
    """Seguimiento mensual de cobranza o renovaciones"""
    mes: str
    mes_num: int
    meta: float = 0
    cobrado: float = 0
    pct: float = 0
    polizas: int = 0


class CobranzaResponse(BaseModel):
    resumen: CobranzaResumen
    deudores: List[DeudorPrima]
    renovaciones: List[RenovacionPendiente]
    canceladas: List[PolizaCancelada]
    alertas: List[AlertaCobranza]
    seguimiento_mensual: List[SeguimientoMensual]
    filtros_disponibles: dict = {}


# ── Conciliación ──────────────────────────────────────────────────
class ResumenConciliacion(BaseModel):
    total: int = 0
    coincide: int = 0
    diferencia: int = 0
    solo_axa: int = 0
    solo_interno: int = 0
    pct_coincidencia: float = 0


class ItemConciliacion(BaseModel):
    poliza: Optional[str] = None
    agente_codigo: Optional[str] = None
    agente_nombre: Optional[str] = None
    ramo: Optional[str] = None
    prima_primer_anio: Optional[float] = None
    es_nueva_axa: Optional[bool] = None
    tipo_poliza_interna: Optional[str] = None
    status: str
    tipo_diferencia: Optional[str] = None


class ConciliacionResponse(BaseModel):
    conciliacion: List[ItemConciliacion]
    resumen: ResumenConciliacion
    periodos: List[str]


# ── Importación ───────────────────────────────────────────────────
class ImportacionResult(BaseModel):
    success: bool
    registros_procesados: int = 0
    registros_nuevos: int = 0
    registros_actualizados: int = 0
    registros_error: int = 0
    errores: List[str] = []
    mensaje: str = ""


# ── Finanzas — Ingresos vs Egresos (Fase 4) ──────────────────────

class IngresoEgresoMensual(BaseModel):
    """Una fila mensual de ingresos vs egresos."""
    mes: str
    mes_num: int = 0
    prima_cobrada: float = 0          # Ingreso
    comision_pagada: float = 0         # Egreso
    margen: float = 0                  # Ingreso - Egreso
    pct_margen: float = 0              # margen/ingreso * 100
    prima_nueva: float = 0
    prima_subsecuente: float = 0
    cancelaciones: float = 0


class ProyeccionCierre(BaseModel):
    """Proyección lineal de cierre del ejercicio."""
    prima_acumulada: float = 0
    meses_transcurridos: int = 0
    promedio_mensual: float = 0
    proyeccion_anual: float = 0
    meta_anual: float = 0
    variacion_vs_meta: float = 0       # (proyeccion - meta) / meta * 100
    tendencia: str = "estable"         # "arriba", "abajo", "estable"
    confianza: float = 0               # R² o similar 0-1


class PresupuestoMensualComp(BaseModel):
    """Comparativo presupuesto IDEAL vs real por mes."""
    mes: str
    meta: float = 0
    real: float = 0
    variacion: float = 0               # (real-meta)/meta * 100
    acumulado_meta: float = 0
    acumulado_real: float = 0


class TendenciaAnual(BaseModel):
    """Línea de tendencia para comparativo interanual."""
    mes: str
    anio_anterior: float = 0
    anio_actual: float = 0
    meta: float = 0
    acum_anterior: float = 0
    acum_actual: float = 0
    acum_meta: float = 0


class ResumenFinanciero(BaseModel):
    """KPIs financieros principales."""
    prima_cobrada_total: float = 0
    comision_total: float = 0
    margen_total: float = 0
    pct_margen: float = 0
    meta_anual: float = 0
    pct_cumplimiento: float = 0
    proyeccion_cierre: float = 0
    variacion_interanual: float = 0
    mejor_mes: Optional[str] = None
    peor_mes: Optional[str] = None


class FinanzasResponse(BaseModel):
    resumen: ResumenFinanciero
    ingresos_egresos: List[IngresoEgresoMensual]
    proyeccion: ProyeccionCierre
    presupuesto: List[PresupuestoMensualComp]
    tendencia: List[TendenciaAnual]
    filtros_disponibles: dict = {}


# ── Contratante (Fase 5.1) ────────────────────────────────────────

class ContratanteBase(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    domicilio: Optional[str] = None
    notas: Optional[str] = None
    referido_por_id: Optional[int] = None
    agente_id: Optional[int] = None


class ContratanteCreate(ContratanteBase):
    pass


class ContratanteOut(ContratanteBase):
    id: int
    num_polizas: int = 0
    prima_total: float = 0
    referido_por_nombre: Optional[str] = None
    created_at: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Solicitud (Fase 5.2) ─────────────────────────────────────────

class SolicitudBase(BaseModel):
    folio: Optional[str] = None
    agente_id: Optional[int] = None
    contratante_id: Optional[int] = None
    ramo: Optional[str] = None
    plan: Optional[str] = None
    suma_asegurada: Optional[float] = None
    prima_estimada: Optional[float] = None
    estado: str = "TRAMITE"
    fecha_solicitud: Optional[str] = None
    notas: Optional[str] = None


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudUpdate(BaseModel):
    estado: Optional[str] = None
    fecha_emision: Optional[str] = None
    fecha_pago: Optional[str] = None
    poliza_id: Optional[int] = None
    notas: Optional[str] = None


class SolicitudOut(SolicitudBase):
    id: int
    poliza_id: Optional[int] = None
    fecha_emision: Optional[str] = None
    fecha_pago: Optional[str] = None
    agente_nombre: Optional[str] = None
    contratante_nombre: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    model_config = {"from_attributes": True}


class PipelineResumen(BaseModel):
    total: int = 0
    tramite: int = 0
    emitida: int = 0
    pagada: int = 0
    rechazada: int = 0
    cancelada: int = 0
    prima_estimada_total: float = 0
    prima_pagada_total: float = 0


class SolicitudesResponse(BaseModel):
    solicitudes: List[SolicitudOut]
    pipeline: PipelineResumen


# ── Distribución de comisiones (Fase 5.3) ─────────────────────────

class DistribucionBase(BaseModel):
    agente_id: int
    sub_agente_id: Optional[int] = None
    nombre_beneficiario: Optional[str] = None
    porcentaje: float
    ramo: Optional[str] = None
    tipo: str = "SUBAGENTE"


class DistribucionCreate(DistribucionBase):
    pass


class DistribucionOut(DistribucionBase):
    id: int
    activo: int = 1
    agente_nombre: Optional[str] = None
    sub_agente_nombre: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Configuración (Fase 5.5) ─────────────────────────────────────

class ConfiguracionItem(BaseModel):
    clave: str
    valor: Optional[str] = None
    tipo: str = "texto"
    grupo: Optional[str] = None
    descripcion: Optional[str] = None


class ConfiguracionUpdate(BaseModel):
    valor: str


class ConfiguracionResponse(BaseModel):
    configuraciones: List[ConfiguracionItem]
    grupos: List[str]

