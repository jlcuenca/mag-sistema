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
