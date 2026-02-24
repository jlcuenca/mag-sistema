"""
Módulo de base de datos: SQLAlchemy + SQLite para MAG Sistema
v0.2.0 — Modelo enriquecido con datos del Reporte Cubo 2025
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Date, DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import os

# ── Configuración ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema", "data", "mag.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ══════════════════════════════════════════════════════════════════
# CATÁLOGOS
# ══════════════════════════════════════════════════════════════════

class Segmento(Base):
    """Segmentos comerciales (ALFA TOP INTEGRAL, BETA1, OMEGA, etc.)"""
    __tablename__ = "segmentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)   # 'ALFA TOP INTEGRAL'
    agrupado = Column(String(20), nullable=False)               # 'ALFA'
    orden = Column(Integer, default=0)

    agentes = relationship("Agente", back_populates="segmento_rel")


class Agente(Base):
    __tablename__ = "agentes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_agente = Column(String(20), unique=True, nullable=False)
    nombre_completo = Column(String(200), nullable=False)
    rol = Column(String(50), default="Agente")
    situacion = Column(String(50), default="ACTIVO")
    fecha_alta = Column(String(10))
    fecha_cancelacion = Column(String(10))
    territorio = Column(String(100))
    oficina = Column(String(100))
    gerencia = Column(String(100))
    promotor = Column(String(100))
    nombre_promotoria = Column(String(200), default="MAG")
    centro_costos = Column(String(20))
    telefono = Column(String(20))
    email = Column(String(200))

    # ── Campos nuevos (Reporte Cubo / VISTAS CUITLAHUAC) ──
    segmento_id = Column(Integer, ForeignKey("segmentos.id"))
    segmento_nombre = Column(String(50))        # Texto directo: 'ALFA TOP INTEGRAL'
    segmento_agrupado = Column(String(20))      # 'ALFA', 'BETA', 'OMEGA'
    gestion_comercial = Column(String(100))     # 'ALFA/MARIA ESTHER', 'MARIO FLORES'
    lider_codigo = Column(String(20))           # Código del líder: '63931'
    estado = Column(String(30))                 # 'ACTIVO', '0' (dato interno AXA)
    asociado = Column(String(100))              # Asociación territorial

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    polizas = relationship("Poliza", back_populates="agente")
    segmento_rel = relationship("Segmento", back_populates="agentes")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    ramo_codigo = Column(Integer, nullable=False)
    ramo_nombre = Column(String(100), nullable=False)
    plan = Column(String(100))
    gama = Column(String(50))
    registro_cnsf = Column(String(50))

    __table_args__ = (UniqueConstraint("ramo_codigo", "plan", "gama"),)

    polizas = relationship("Poliza", back_populates="producto")


# ══════════════════════════════════════════════════════════════════
# TABLA PRINCIPAL DE PÓLIZAS
# ══════════════════════════════════════════════════════════════════

class Poliza(Base):
    __tablename__ = "polizas"

    id = Column(Integer, primary_key=True, index=True)
    poliza_original = Column(String(30), nullable=False)
    poliza_estandar = Column(String(30), nullable=False)
    version = Column(Integer, default=0)
    solicitud = Column(String(30))
    archivo_pdf = Column(String(200))

    agente_id = Column(Integer, ForeignKey("agentes.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    asegurado_nombre = Column(String(200))
    contratante_nombre = Column(String(200))
    rfc = Column(String(20))
    codigo_postal = Column(String(10))
    telefono = Column(String(20))
    email = Column(String(200))
    num_asegurados = Column(Integer, default=1)

    fecha_emision = Column(String(10))
    fecha_inicio = Column(String(10), nullable=False)
    fecha_fin = Column(String(10))

    moneda = Column(String(5), default="MN")
    prima_total = Column(Float)
    prima_neta = Column(Float)
    iva = Column(Float, default=0)
    recargo = Column(Float, default=0)
    derecho_poliza = Column(Float)
    suma_asegurada = Column(Float)
    deducible = Column(Float)
    coaseguro = Column(Float)
    forma_pago = Column(String(20))
    tipo_pago = Column(String(30))
    status_recibo = Column(String(50))
    plazo_pago = Column(String(30))
    tope = Column(Float)
    zona = Column(String(20))
    red = Column(String(30))
    tabulador = Column(String(30))
    maternidad = Column(String(20))
    cobertura = Column(Text)
    gama = Column(String(50))

    es_nueva = Column(Boolean)
    tipo_poliza = Column(String(20))      # NUEVA, SUBSECUENTE, NO_APLICA
    tipo_prima = Column(String(20))       # BASICA, EXCEDENTE (Vida)
    pct_comision = Column(Float)
    poliza_padre_id = Column(Integer, ForeignKey("polizas.id"))
    es_reexpedicion = Column(Boolean, default=False)
    mystatus = Column(String(50))

    periodo_aplicacion = Column(String(7))
    anio_aplicacion = Column(Integer)
    fuente = Column(String(50), default="EXCEL_IMPORT")
    notas = Column(Text)

    # ── Campos nuevos (Reporte Cubo 2025) ──────────────────────
    segmento = Column(String(50))               # 'ALFA TOP INTEGRAL', 'OMEGA', etc.
    gestion_comercial = Column(String(100))     # 'ALFA/MARIA ESTHER'
    lider_codigo = Column(String(20))           # '63931'
    clasificacion_cy = Column(String(30))       # 'CY SUBSECUENTE', 'CY ANUAL'
    estatus_cubo = Column(String(50))           # 'POLIZA PAGADA', 'POLIZA AL CORRIENTE', etc.
    estatus_detalle = Column(String(100))       # 'FALTA DE PAGO', 'NO TOMADA', etc.
    nueva_poliza_flag = Column(Integer)         # 1 = nueva (flag del Cubo)

    # Primas multi-métrica
    neta_total_contrato = Column(Float)         # Prima neta total del contrato
    neta_acumulada = Column(Float)              # Prima neta acumulada pagada
    neta_forma_pago = Column(Float)             # Prima neta según forma de pago
    neta_sin_forma = Column(Float)              # Prima neta sin ajuste de forma de pago
    neta_cancelacion = Column(Float)            # Prima con impacto de cancelación

    # Fechas adicionales de cobranza
    fecha_primer_pago = Column(String(10))
    fecha_ultimo_pago = Column(String(10))

    # Período de confirmación
    anio_conf = Column(Integer)
    mes_conf = Column(Integer)

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    agente = relationship("Agente", back_populates="polizas")
    producto = relationship("Producto", back_populates="polizas")
    recibos = relationship("Recibo", back_populates="poliza")


# ══════════════════════════════════════════════════════════════════
# RECIBOS (granularidad a nivel pago — Hoja DETALLE del Cubo)
# ══════════════════════════════════════════════════════════════════

class Recibo(Base):
    __tablename__ = "recibos"

    id = Column(Integer, primary_key=True, index=True)
    poliza_id = Column(Integer, ForeignKey("polizas.id"))
    poliza_numero = Column(String(30))          # Número de póliza (para cruces)

    # Datos del recibo
    fecha_recibo = Column(String(10))
    anio_apli = Column(Integer)
    mes_conf = Column(Integer)
    anio_conf = Column(Integer)
    comprobante = Column(String(30))            # 'DS175679'

    # Primas del recibo
    neta_acumulada = Column(Float)
    neta_forma_pago = Column(Float)
    neta_sin_forma = Column(Float)
    neta_cancelacion = Column(Float)

    # Contexto (desnormalizado para reportes rápidos)
    agente_codigo = Column(String(20))
    nombre_agente = Column(String(200))
    ramo = Column(Integer)
    plan = Column(String(100))
    segmento = Column(String(50))
    contratante = Column(String(200))
    estatus = Column(String(50))
    estatus_detalle = Column(String(100))

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())

    poliza = relationship("Poliza", back_populates="recibos")


# ══════════════════════════════════════════════════════════════════
# INDICADORES AXA
# ══════════════════════════════════════════════════════════════════

class IndicadorAxa(Base):
    __tablename__ = "indicadores_axa"

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String(7), nullable=False)
    fecha_recepcion = Column(String(10))
    poliza = Column(String(30))
    agente_codigo = Column(String(20))
    ramo = Column(String(100))
    num_asegurados = Column(Integer)
    polizas_equivalentes = Column(Float)
    prima_primer_anio = Column(Float)
    antiguedad_axa = Column(String(10))
    fecha_inicio_vigencia = Column(String(10))
    es_nueva_axa = Column(Boolean)
    reconocimiento_antiguedad = Column(Boolean)
    encontrada_en_base = Column(Boolean)
    diferencia_clasificacion = Column(Text)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())


class Conciliacion(Base):
    __tablename__ = "conciliaciones"

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String(7), nullable=False)
    fecha_conciliacion = Column(String(30), default=lambda: datetime.now().isoformat())
    poliza_id = Column(Integer, ForeignKey("polizas.id"))
    indicador_axa_id = Column(Integer, ForeignKey("indicadores_axa.id"))
    status = Column(String(30))
    tipo_diferencia = Column(Text)
    clasificacion_interna = Column(String(20))
    clasificacion_axa = Column(String(20))
    prima_interna = Column(Float)
    prima_axa = Column(Float)
    resuelto = Column(Boolean, default=False)
    notas_resolucion = Column(Text)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())


class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, nullable=False)
    periodo = Column(String(7))
    agente_id = Column(Integer, ForeignKey("agentes.id"))
    meta_polizas_vida = Column(Integer)
    meta_prima_vida = Column(Float)
    meta_polizas_gmm = Column(Integer)
    meta_asegurados_gmm = Column(Integer)
    meta_prima_gmm = Column(Float)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())


class Importacion(Base):
    __tablename__ = "importaciones"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)
    archivo_nombre = Column(String(200))
    registros_procesados = Column(Integer)
    registros_nuevos = Column(Integer)
    registros_actualizados = Column(Integer)
    registros_error = Column(Integer)
    errores_detalle = Column(Text)
    usuario = Column(String(100))
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())


# ── Dependency ─────────────────────────────────────────────────────
def get_db():
    """Dependency injection para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas si no existen"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Base de datos lista en: {DB_PATH}")
