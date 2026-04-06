"""
Módulo de base de datos: SQLAlchemy para MAG Sistema
v0.3.0 — Soporta SQLite (local) y PostgreSQL (GCP Cloud SQL)
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
# En producción (GCP): DATABASE_URL = "postgresql://user:pass@host/db"
# En desarrollo local: usa SQLite por defecto
_ENV_DB_URL = os.getenv("DATABASE_URL")

if _ENV_DB_URL:
    # PostgreSQL en Cloud SQL (producción)
    DATABASE_URL = _ENV_DB_URL
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
    )
    print(f"[MAG-DB] Conectando a PostgreSQL...")
else:
    # SQLite local (desarrollo)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "sistema", "data", "mag.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    print(f"[MAG-DB] Usando SQLite local: {DB_PATH}")

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
    gestion_id = Column(Integer, ForeignKey("gestiones_comerciales.id"))  # FK Fase 3.5

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    polizas = relationship("Poliza", back_populates="agente")
    segmento_rel = relationship("Segmento", back_populates="agentes")
    gestion_rel = relationship("GestionComercial", back_populates="agentes")


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

    # ── Refactor v2.0: Vinculación con Solicitud ──────────────
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"))
    solicitud_nosol = Column(String(30), index=True)             # NOSOL para cruces

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

    # ── Campos calculados (reglas del AUTOMATICO) ──────────────
    largo_poliza = Column(Integer)                   # BG: LEN(poliza)
    raiz_poliza_6 = Column(String(6))               # BH: LEFT(poliza,6)
    terminacion = Column(String(2))                  # BI: RIGHT(poliza,2)
    num_reexpediciones = Column(Integer)             # BF: COUNTIF de raíz
    primer_anio = Column(String(50))                 # BJ: "PRIMER AÑO 2025", etc.
    id_compuesto = Column(String(60))               # BT: poliza+fecha_inicio
    fecha_aplicacion = Column(String(10))            # BU/BK: FEC APLI
    mes_aplicacion = Column(String(20))             # BL: MES APLI (ENERO, etc.)
    pendientes_pago = Column(String(100))           # BV: etiqueta o ""
    trimestre = Column(String(20))                  # CA: Q1, Q2, Q3, Q4
    prima_acumulada_basica = Column(Float)           # CF: SUMIFS prima pagada
    flag_pagada = Column(Integer)                    # CI: 0/1
    flag_nueva_formal = Column(Integer)             # CJ: 0/1
    prima_anual_pesos = Column(Float)               # CM: prima convertida a MXN
    equivalencias_emitidas = Column(Float)           # CN: EQUIV
    equivalencias_pagadas = Column(Float)            # CO: EQUIV PAGADA
    flag_cancelada = Column(Integer)                 # CP: 0/1
    prima_proporcional = Column(Float)              # CU: prima proporcional al tiempo
    condicional_prima = Column(String(20))          # CV/CN: "OK"/"Cancelada"

    # ── Fase 5.1: Link to Contratante ──
    contratante_id = Column(Integer, ForeignKey("contratantes.id"))

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    agente = relationship("Agente", back_populates="polizas")
    producto = relationship("Producto", back_populates="polizas")
    recibos = relationship("Recibo", back_populates="poliza")
    contratante_rel = relationship("Contratante", back_populates="polizas")
    solicitud_rel = relationship("Solicitud", foreign_keys=[solicitud_id],
                                 viewonly=True, uselist=False)


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


# ══════════════════════════════════════════════════════════════════
# PAGOS (PAGTOTAL — registro de pagos completados)
# ══════════════════════════════════════════════════════════════════

class Pago(Base):
    """Registro de pagos desde PAGTOTAL — una fila por pago realizado."""
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    poliza_numero = Column(String(30), index=True, nullable=False)
    endoso = Column(String(30))
    agente_codigo = Column(String(20), index=True)
    contratante = Column(String(200))
    ramo = Column(String(100))
    moneda = Column(String(10), default="MN")
    fecha_inicio = Column(String(10))
    fecha_aplicacion = Column(String(10), index=True)
    comprobante = Column(String(30))
    prima_neta = Column(Float, default=0)
    prima_total = Column(Float, default=0)
    comision = Column(Float, default=0)
    comision_derecho = Column(Float, default=0)
    comision_recargo = Column(Float, default=0)
    comision_total = Column(Float, default=0)
    promotor = Column(String(20))
    poliza_match = Column(String(30), index=True)
    anio_aplicacion = Column(Integer, index=True)
    periodo_aplicacion = Column(String(7))
    fuente = Column(String(50), default="PAGTOTAL")
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())

    # ── Columnas calculadas — Reglas PRIMA PAGADA (R–AY) ──────────
    # Temporales (derivadas de fecha_aplicacion)
    mes_aplicacion_nombre = Column(String(20))       # R: UPPER(TEXT(H2,"MMMM"))
    anio_aplicacion_calc = Column(Integer)            # S: YEAR(H2)
    mes_numero = Column(Integer)                      # AT: MONTH(H2)
    trimestre = Column(String(20))                    # AQ: Q1, Q2, Q3, Q4

    # Identificación de póliza
    id_compuesto = Column(String(60))                 # T: poliza&fecini
    poliza_estandar = Column(String(30))              # AF: IF(largo=11,LEFT(E,8),E)
    poliza_6 = Column(String(6))                      # AY: LEFT(E2,6)
    largo_poliza = Column(Integer)                    # AC: LEN(E2)
    id_vida = Column(String(60))                      # AX: poliza_estandar&perini

    # Enriquecimiento del agente (JOINs con agentes)
    nombre_agente = Column(String(200))               # W: XLOOKUP→DIRECTORIO!B
    nombre_promotor = Column(String(200))             # X: XLOOKUP→DIRECTORIO!AF
    segmento = Column(String(50))                     # Y: XLOOKUP→DIRECTORIO!G
    segmento_agrupado = Column(String(20))            # Z: ALFA/BETA/OMEGA
    gestion_comercial = Column(String(100))           # AA: XLOOKUP→DIRECTORIO!K
    estatus_agente = Column(String(50))               # AV: estatus agente
    segmento_indicadores = Column(String(50))         # AW: segmento indicadores

    # Enriquecimiento de póliza (JOINs con polizas)
    fecini_poliza = Column(String(10))                # U: fecha_inicio de la póliza
    primer_anio = Column(String(50))                  # V: PRIMER AÑO
    primer_anio_vida = Column(String(50))             # AD: PRIMER AÑO VIDA
    cuenta_o_no = Column(Integer)                     # AB: flag_nueva_formal
    nueva_no_nueva = Column(Integer)                  # AI: es_nueva (0/1)
    num_asegurados = Column(Integer)                  # AO: ASEGS de la póliza
    cruze_vs_aut = Column(String(30))                 # AE: ¿existe en polizas?
    poliza_exists = Column(String(30))                # AM: ¿existe en polizas?

    # Datos fijos (de la póliza vinculada)
    primer_anio_fijo = Column(String(50))             # AJ: primer_anio fijo
    mes_apli_fijo = Column(String(20))                # AK: mes_aplicacion fijo
    anio_apli_fijo = Column(Integer)                  # AL: anio_aplicacion fijo

    # Clasificación
    aportacion = Column(String(20))                   # AG: BASICA/EXCEDENTE
    pct_comision = Column(Float)                      # AH: totcomision/neta


class GestionComercial(Base):
    """Gestiones comerciales — líderes y asignación de agentes (Fase 3.5)"""
    __tablename__ = "gestiones_comerciales"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)   # 'ALFA/MARIA ESTHER'
    lider_codigo = Column(String(20))                            # '63931'
    lider_nombre = Column(String(200))
    tipo = Column(String(30))                                    # 'ALFA', 'BETA', 'OMEGA', 'DIRECTA'
    activa = Column(Boolean, default=True)
    num_agentes = Column(Integer, default=0)
    meta_anual_vida = Column(Float, default=0)
    meta_anual_gmm = Column(Float, default=0)
    notas = Column(Text)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())

    agentes = relationship("Agente", back_populates="gestion_rel")


class Presupuesto(Base):
    """Presupuestos mensuales/anuales por ramo y agente (Fase 3.4)"""
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, nullable=False)
    periodo = Column(String(7))                    # NULL=anual, '2026-01'=mensual
    ramo = Column(String(10))                      # 'VIDA', 'GMM', NULL=total
    agente_id = Column(Integer, ForeignKey("agentes.id"))
    gestion_id = Column(Integer, ForeignKey("gestiones_comerciales.id"))

    meta_polizas = Column(Integer, default=0)
    meta_equivalentes = Column(Float, default=0)
    meta_asegurados = Column(Integer, default=0)
    meta_prima_nueva = Column(Float, default=0)
    meta_prima_subsecuente = Column(Float, default=0)
    meta_prima_total = Column(Float, default=0)

    real_polizas = Column(Integer, default=0)
    real_equivalentes = Column(Float, default=0)
    real_asegurados = Column(Integer, default=0)
    real_prima_nueva = Column(Float, default=0)
    real_prima_subsecuente = Column(Float, default=0)
    real_prima_total = Column(Float, default=0)

    variacion_pct = Column(Float, default=0)       # (real-meta)/meta * 100
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())


class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, nullable=False)
    periodo = Column(String(7))
    agente_id = Column(Integer, ForeignKey("agentes.id"))
    meta_polizas_vida = Column(Integer)
    meta_equiv_vida = Column(Float)                # Equivalentes Vida (3.3)
    meta_prima_vida = Column(Float)
    meta_polizas_gmm = Column(Integer)
    meta_asegurados_gmm = Column(Integer)
    meta_prima_gmm = Column(Float)
    # Faltantes calculados (3.3)
    faltante_polizas_vida = Column(Integer)
    faltante_equiv_vida = Column(Float)
    faltante_prima_vida = Column(Float)
    faltante_polizas_gmm = Column(Integer)
    faltante_prima_gmm = Column(Float)
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


# ── Contratante (Fase 5.1) ──────────────────────────────────────
class Contratante(Base):
    __tablename__ = "contratantes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    rfc = Column(String(20))
    telefono = Column(String(20))
    email = Column(String(200))
    domicilio = Column(Text)
    notas = Column(Text)
    referido_por_id = Column(Integer, ForeignKey("contratantes.id"))
    agente_id = Column(Integer, ForeignKey("agentes.id"))       # Agente asignado

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    # Self-referencing: quién lo refirió
    referidos = relationship("Contratante", backref="referido_por", remote_side=[id])
    polizas = relationship("Poliza", back_populates="contratante_rel")
    solicitudes = relationship("Solicitud", back_populates="contratante_rel")


# ══════════════════════════════════════════════════════════════════
# SOLICITUDES — Entidad Raíz del Sistema (Refactor v2.0)
# ══════════════════════════════════════════════════════════════════

class Solicitud(Base):
    """Solicitud de seguro — eje principal del sistema.
    Toda actividad comienza como solicitud y puede convertirse en póliza.
    Datos crudos provienen de VW_CONCENTRADO_ETAPAS + Concentrado AXA."""
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)

    # ── Datos Crudos Fijos (del CSV/Excel AXA) ──────────────────
    nosol = Column(String(30), unique=True, index=True)          # Número de solicitud AXA
    folio = Column(String(30), index=True)                       # Folio alterno (compat legacy)
    nomramo = Column(String(50), index=True)                     # SALUD, VIDA
    fecrecepcion = Column(String(30))                            # Fecha recepción AXA
    contratante_nombre = Column(String(300))                     # Nombre contratante
    dia_recepcion = Column(Integer)
    mes_recepcion = Column(Integer, index=True)
    ano_recepcion = Column(Integer, index=True)
    idagente = Column(String(20), index=True)                    # Código del agente
    nuevo = Column(Integer)                                      # 1=nueva, 0=reingreso
    antaxa = Column(Integer)                                     # Antigüedad AXA
    reingreso = Column(Integer)
    contasol = Column(Integer)                                   # Contador solicitud
    numsolicitantes = Column(Integer, default=1)                 # Asegurados solicitados
    fecha_sistema = Column(String(30))

    # ── Datos del Concentrado completo (60 cols) ────────────────
    ramo = Column(String(100))                                   # Ramo / Subramo
    subramo = Column(String(50))
    plan = Column(String(100))                                   # Producto
    forma_pago = Column(String(30))
    suma_asegurada = Column(Float)
    prima_estimada = Column(Float)                               # Prima contratada
    prima_contratada = Column(Float)                             # PRIMA_CON
    comision_total_sol = Column(Float)                           # COM_TOT
    prima_pagada_sol = Column(Float)                             # PRI_PAG
    num_revires = Column(Integer)                                # Devoluciones
    f_captura_agente = Column(String(30))
    f_envio_poliza = Column(String(30))
    f_fin_sla = Column(String(30))
    territorio = Column(String(100))
    zona = Column(String(100))
    oficina = Column(String(100))
    canal = Column(String(50))
    promotor_codigo = Column(String(20))
    promotor_nombre = Column(String(200))

    # ── Datos Calculados (Reglas de Negocio) ─────────────────────
    ramo_normalizado = Column(String(10))                        # S1: 'VIDA' | 'GMM'
    estado = Column(String(30), default="TRAMITE")               # S2: TRAMITE|EMITIDA|PAGADA|RECHAZADA|CANCELADA
    dias_tramite = Column(Integer)                               # (fecetapa - fecrecepcion).days
    alerta_atorada = Column(Integer, default=0)                  # S4: >15 días sin movimiento
    tasa_conversion_agente = Column(Float)                       # S5: batch calculado
    sla_cumplido = Column(Integer)                               # Dentro del SLA AXA?
    tipo_rechazo = Column(String(50))                            # Clasificación rechazo

    # ── Última etapa (desnormalizado para queries rápidos) ──────
    ultima_etapa = Column(String(50))
    ultima_subetapa = Column(String(50))
    fecha_ultima_etapa = Column(String(30))
    observaciones_etapa = Column(Text)

    # ── Vinculaciones ───────────────────────────────────────────
    poliza_numero = Column(String(30))                           # Póliza emitida (o NULL)
    poliza_id = Column(Integer)                                  # Legacy (no FK)
    agente_id = Column(Integer, ForeignKey("agentes.id"))
    contratante_id = Column(Integer, ForeignKey("contratantes.id"))

    # Legacy compat
    fecha_solicitud = Column(String(10))
    fecha_emision = Column(String(10))
    fecha_pago = Column(String(10))
    notas = Column(Text)

    # ── Auditoría ───────────────────────────────────────────────
    fuente = Column(String(50), default="VW_CONCENTRADO")
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())

    # ── Relaciones ──────────────────────────────────────────────
    agente_rel = relationship("Agente", foreign_keys=[agente_id])
    contratante_rel = relationship("Contratante", back_populates="solicitudes",
                                   foreign_keys=[contratante_id])
    etapas = relationship("EtapaSolicitud", back_populates="solicitud_rel",
                          order_by="EtapaSolicitud.fecetapa",
                          foreign_keys="[EtapaSolicitud.solicitud_id]")


# ── Distribución de Comisiones (Fase 5.3) ────────────────────────
class DistribucionComision(Base):
    __tablename__ = "distribuciones_comision"

    id = Column(Integer, primary_key=True, index=True)
    agente_id = Column(Integer, ForeignKey("agentes.id"), nullable=False)
    sub_agente_id = Column(Integer, ForeignKey("agentes.id"))
    nombre_beneficiario = Column(String(200))                   # Si no es agente formal
    porcentaje = Column(Float, nullable=False)                  # 0-100
    ramo = Column(String(100))                                  # NULL=todos, 'VIDA', 'GMM'
    tipo = Column(String(30), default="SUBAGENTE")              # SUBAGENTE, VENDEDOR, PROMOTOR
    activo = Column(Integer, default=1)

    created_at = Column(String(30), default=lambda: datetime.now().isoformat())


# ── Etapas de Solicitud (VW_CONCENTRADO_ETAPAS) — Timeline ──────
class EtapaSolicitud(Base):
    """Registro de etapas del pipeline — cada fila es un evento en el timeline.
    La cabecera vive en Solicitud; esta tabla es el historial de movimientos."""
    __tablename__ = "etapas_solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    nosol = Column(String(30), index=True, nullable=False)       # Número de solicitud
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id")) # FK a cabecera
    nomramo = Column(String(50), index=True)                     # SALUD, VIDA
    fecrecepcion = Column(String(30))                            # Fecha de recepción
    contratante = Column(String(300))
    dia_recepcion = Column(Integer)
    mes_recepcion = Column(Integer, index=True)
    ano_recepcion = Column(Integer, index=True)
    etapa = Column(String(50), index=True)                       # POLIZA_ENVIADA, RECHAZO_EMISION, etc.
    subetapa = Column(String(50))
    fecetapa = Column(String(30))                                # Fecha de la etapa
    dia_etapa = Column(Integer)
    mes_etapa = Column(Integer)
    ano_etapa = Column(Integer)
    observaciones = Column(Text)
    idagente = Column(String(20), index=True)                    # Código del agente
    nuevo = Column(Integer)                                      # 1=nuevo, 0=reingreso
    antaxa = Column(Integer)                                     # 1=antigüedad AXA
    reingreso = Column(Integer)
    contasol = Column(Integer)                                   # Contador de solicitud
    poliza = Column(String(30))                                  # Póliza emitida o PENDIENTE
    numsolicitantes = Column(Integer, default=1)
    fecha_sistema = Column(String(30))
    # Campos calculados
    dias_tramite = Column(Integer)                               # Días entre recepción y etapa
    fuente = Column(String(50), default="VW_CONCENTRADO")
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())

    # Relación a cabecera
    solicitud_rel = relationship("Solicitud", back_populates="etapas",
                                 foreign_keys=[solicitud_id])


# ── Configuración Dinámica (Fase 5.5) ───────────────────────────
class Configuracion(Base):
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text)
    tipo = Column(String(20), default="texto")                  # texto, numero, json, booleano
    grupo = Column(String(50))                                  # umbrales, tipos_cambio, catalogos
    descripcion = Column(String(300))
    updated_at = Column(String(30), default=lambda: datetime.now().isoformat())


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
    db_desc = DATABASE_URL.split("@")[0].split("://")[0] if "@" in DATABASE_URL else DATABASE_URL
    print(f"✅ Base de datos lista ({db_desc})")
