"""
Routers FastAPI para MAG Sistema
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case
from typing import Optional, List
import pandas as pd
import io, os, re
from collections import defaultdict

from .database import get_db, Agente, Poliza, Producto, IndicadorAxa, Meta, Importacion, Segmento, Recibo, Conciliacion
from .schemas import (
    AgenteOut, AgenteCreate,
    PolizaOut, PolizaCreate, PolizaListResponse,
    DashboardResponse, KPIs, ProduccionMensual, TopAgente, DistribucionGama,
    ConciliacionResponse, ResumenConciliacion, ItemConciliacion,
    ImportacionResult
)
from .rules import normalizar_poliza, calcular_mystatus, es_reexpedicion, agrupar_segmento, clasificar_cy

# ═══════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════
router_dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router_dashboard.get("", response_model=DashboardResponse)
def get_dashboard(
    anio: int = Query(2025, description="Año de análisis"),
    db: Session = Depends(get_db)
):
    """KPIs principales, producción mensual, top agentes y distribución por gama."""

    # ── Consulta base ──
    polizas = db.execute(text("""
        SELECT p.*, pr.ramo_codigo, pr.ramo_nombre, pr.plan,
               a.nombre_completo as agente_nombre, a.codigo_agente,
               a.oficina, a.gerencia, a.territorio,
               a.segmento_nombre, a.segmento_agrupado
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.anio_aplicacion = :anio
    """), {"anio": anio}).mappings().all()

    # ── KPIs ──
    nuevas_vida  = [p for p in polizas if p["ramo_codigo"]==11 and p["tipo_poliza"]=="NUEVA" and p["tipo_prima"]=="BASICA"]
    nuevas_gmm   = [p for p in polizas if p["ramo_codigo"]==34 and p["tipo_poliza"]=="NUEVA"]
    subs_vida    = [p for p in polizas if p["ramo_codigo"]==11 and p["tipo_poliza"]=="SUBSECUENTE"]
    subs_gmm     = [p for p in polizas if p["ramo_codigo"]==34 and p["tipo_poliza"]=="SUBSECUENTE"]
    canceladas   = [p for p in polizas if p["status_recibo"] not in ("PAGADA", "AL CORRIENTE", None)]

    meta = db.execute(text("SELECT * FROM metas WHERE anio=:a AND periodo IS NULL"), {"a": anio}).mappings().first()

    kpis = KPIs(
        polizas_nuevas_vida   = len(nuevas_vida),
        prima_nueva_vida      = sum(p["prima_neta"] or 0 for p in nuevas_vida),
        polizas_nuevas_gmm    = len(nuevas_gmm),
        asegurados_nuevos_gmm = sum(p["num_asegurados"] or 1 for p in nuevas_gmm),
        prima_nueva_gmm       = sum(p["prima_neta"] or 0 for p in nuevas_gmm),
        prima_subsecuente_vida= sum(p["prima_neta"] or 0 for p in subs_vida),
        prima_subsecuente_gmm = sum(p["prima_neta"] or 0 for p in subs_gmm),
        polizas_canceladas    = len(canceladas),
        total_polizas         = len(polizas),
        meta_vida             = meta["meta_polizas_vida"] if meta else 0,
        meta_gmm              = meta["meta_polizas_gmm"] if meta else 0,
        meta_prima_vida       = meta["meta_prima_vida"] if meta else 0,
        meta_prima_gmm        = meta["meta_prima_gmm"] if meta else 0,
    )

    # ── Producción mensual ──
    mensual_raw = db.execute(text("""
        SELECT p.periodo_aplicacion as periodo,
               SUM(CASE WHEN pr.ramo_codigo=11 AND p.tipo_poliza='NUEVA' THEN 1 ELSE 0 END) as polizas_vida,
               SUM(CASE WHEN pr.ramo_codigo=34 AND p.tipo_poliza='NUEVA' THEN 1 ELSE 0 END) as polizas_gmm,
               SUM(CASE WHEN pr.ramo_codigo=11 AND p.tipo_poliza='NUEVA' THEN p.prima_neta ELSE 0 END) as prima_vida,
               SUM(CASE WHEN pr.ramo_codigo=34 AND p.tipo_poliza='NUEVA' THEN p.prima_neta ELSE 0 END) as prima_gmm
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE p.anio_aplicacion = :anio
        GROUP BY p.periodo_aplicacion
        ORDER BY p.periodo_aplicacion
    """), {"anio": anio}).mappings().all()

    produccion_mensual = [
        ProduccionMensual(
            periodo=r["periodo"] or "",
            polizas_vida=r["polizas_vida"] or 0,
            polizas_gmm=r["polizas_gmm"] or 0,
            prima_vida=round(r["prima_vida"] or 0, 2),
            prima_gmm=round(r["prima_gmm"] or 0, 2),
        ) for r in mensual_raw
    ]

    # ── Top agentes ──
    top_raw = db.execute(text("""
        SELECT a.nombre_completo, a.codigo_agente, a.oficina,
               a.segmento_nombre as segmento,
               COUNT(CASE WHEN p.tipo_poliza='NUEVA' THEN 1 END) as polizas_nuevas,
               SUM(CASE WHEN p.tipo_poliza='NUEVA' THEN p.prima_neta ELSE 0 END) as prima_total
        FROM polizas p
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.anio_aplicacion = :anio
        GROUP BY a.id
        ORDER BY prima_total DESC
        LIMIT 10
    """), {"anio": anio}).mappings().all()

    top_agentes = [
        TopAgente(
            nombre_completo=r["nombre_completo"],
            codigo_agente=r["codigo_agente"],
            oficina=r["oficina"],
            segmento=r["segmento"],
            polizas_nuevas=r["polizas_nuevas"] or 0,
            prima_total=round(r["prima_total"] or 0, 2),
        ) for r in top_raw
    ]

    # ── Distribución por gama GMM ──
    gama_raw = db.execute(text("""
        SELECT p.gama, COUNT(*) as total, SUM(p.prima_neta) as prima
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE pr.ramo_codigo=34 AND p.anio_aplicacion=:anio AND p.gama IS NOT NULL
        GROUP BY p.gama
    """), {"anio": anio}).mappings().all()

    dist_gama = [
        DistribucionGama(gama=r["gama"], total=r["total"], prima=round(r["prima"] or 0, 2))
        for r in gama_raw
    ]

    return DashboardResponse(
        kpis=kpis,
        produccion_mensual=produccion_mensual,
        top_agentes=top_agentes,
        distribucion_gama=dist_gama,
    )


# ═══════════════════════════════════════════════════════════════════
# PÓLIZAS
# ═══════════════════════════════════════════════════════════════════
router_polizas = APIRouter(prefix="/polizas", tags=["Pólizas"])


@router_polizas.get("", response_model=PolizaListResponse)
def list_polizas(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    ramo: Optional[str] = None,
    tipo: Optional[str] = None,
    agente: Optional[str] = None,
    anio: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    conditions = ["1=1"]
    params: dict = {}

    if ramo == "vida":
        conditions.append("pr.ramo_codigo = 11")
    elif ramo == "gmm":
        conditions.append("pr.ramo_codigo = 34")
    if tipo:
        conditions.append("p.tipo_poliza = :tipo")
        params["tipo"] = tipo.upper()
    if agente:
        conditions.append("a.codigo_agente = :agente")
        params["agente"] = agente
    if anio:
        conditions.append("p.anio_aplicacion = :anio")
        params["anio"] = anio
    if q:
        conditions.append("(p.poliza_original LIKE :q OR p.asegurado_nombre LIKE :q OR a.codigo_agente LIKE :q)")
        params["q"] = f"%{q}%"

    where = " AND ".join(conditions)

    total_row = db.execute(text(f"""
        SELECT COUNT(*) as total
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE {where}
    """), params).mappings().first()
    total = total_row["total"] if total_row else 0

    offset = (page - 1) * limit
    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(f"""
        SELECT p.*,
               pr.ramo_codigo, pr.ramo_nombre, pr.plan,
               a.nombre_completo as agente_nombre, a.codigo_agente,
               a.oficina, a.gerencia, a.territorio
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE {where}
        ORDER BY p.fecha_inicio DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()

    data = [PolizaOut(**dict(r)) for r in rows]
    pages = max(1, -(-total // limit))  # ceil division

    return PolizaListResponse(data=data, total=total, page=page, limit=limit, pages=pages)


@router_polizas.post("", status_code=201)
def create_poliza(poliza: PolizaCreate, db: Session = Depends(get_db)):
    nueva = Poliza(
        poliza_original=poliza.poliza_original,
        poliza_estandar=normalizar_poliza(poliza.poliza_original),
        agente_id=poliza.agente_id,
        producto_id=poliza.producto_id,
        asegurado_nombre=poliza.asegurado_nombre,
        rfc=poliza.rfc,
        fecha_inicio=poliza.fecha_inicio,
        fecha_fin=poliza.fecha_fin,
        prima_total=poliza.prima_total,
        prima_neta=poliza.prima_neta,
        iva=poliza.iva or 0,
        recargo=poliza.recargo or 0,
        suma_asegurada=poliza.suma_asegurada,
        num_asegurados=poliza.num_asegurados or 1,
        forma_pago=poliza.forma_pago,
        tipo_pago=poliza.tipo_pago,
        status_recibo=poliza.status_recibo or "PAGADA",
        gama=poliza.gama,
        tipo_poliza=poliza.tipo_poliza,
        tipo_prima=poliza.tipo_prima,
        mystatus=calcular_mystatus(poliza.status_recibo or "PAGADA"),
        periodo_aplicacion=poliza.fecha_inicio[:7] if poliza.fecha_inicio else None,
        anio_aplicacion=int(poliza.fecha_inicio[:4]) if poliza.fecha_inicio else None,
        fuente="MANUAL",
        notas=poliza.notas,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"success": True, "id": nueva.id}


# ═══════════════════════════════════════════════════════════════════
# AGENTES
# ═══════════════════════════════════════════════════════════════════
router_agentes = APIRouter(prefix="/agentes", tags=["Agentes"])


@router_agentes.get("")
def list_agentes(
    situacion: Optional[str] = None,
    db: Session = Depends(get_db)
):
    where = "WHERE a.situacion = :s" if situacion and situacion != "TODOS" else ""
    params = {"s": situacion} if situacion and situacion != "TODOS" else {}

    rows = db.execute(text(f"""
        SELECT a.*,
               COUNT(p.id) as total_polizas,
               SUM(CASE WHEN p.tipo_poliza='NUEVA' AND p.anio_aplicacion=2025 THEN 1 ELSE 0 END) as polizas_nuevas_2025,
               SUM(CASE WHEN p.tipo_poliza='NUEVA' AND p.anio_aplicacion=2025 THEN p.prima_neta ELSE 0 END) as prima_nueva_2025
        FROM agentes a
        LEFT JOIN polizas p ON p.agente_id = a.id
        {where}
        GROUP BY a.id
        ORDER BY prima_nueva_2025 DESC
    """), params).mappings().all()

    return {"data": [dict(r) for r in rows]}


@router_agentes.post("", status_code=201)
def create_agente(agente: AgenteCreate, db: Session = Depends(get_db)):
    nuevo = Agente(**agente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"success": True, "id": nuevo.id}


# ═══════════════════════════════════════════════════════════════════
# CONCILIACIÓN
# ═══════════════════════════════════════════════════════════════════
router_conciliacion = APIRouter(prefix="/conciliacion", tags=["Conciliación"])


@router_conciliacion.get("", response_model=ConciliacionResponse)
def get_conciliacion(
    periodo: str = Query("2025-07"),
    db: Session = Depends(get_db)
):
    indicadores = db.execute(text("""
        SELECT i.*, a.nombre_completo as agente_nombre
        FROM indicadores_axa i
        LEFT JOIN agentes a ON a.codigo_agente = i.agente_codigo
        WHERE i.periodo = :periodo
    """), {"periodo": periodo}).mappings().all()

    conciliacion = []
    for ind in indicadores:
        poliza_int = db.execute(text("""
            SELECT p.tipo_poliza, pr.ramo_codigo, pr.ramo_nombre
            FROM polizas p
            LEFT JOIN productos pr ON p.producto_id = pr.id
            WHERE p.poliza_estandar = :pe OR p.poliza_original = :po
        """), {"pe": ind["poliza"], "po": ind["poliza"]}).mappings().first()

        if poliza_int:
            coincide = poliza_int["tipo_poliza"] == "NUEVA" and ind["es_nueva_axa"]
            status = "COINCIDE" if coincide else "DIFERENCIA"
            dif = None if coincide else f"Interno: {poliza_int['tipo_poliza']}, AXA: {'NUEVA' if ind['es_nueva_axa'] else 'NO NUEVA'}"
            tipo_pol_int = poliza_int["tipo_poliza"]
        else:
            status = "SOLO_AXA"
            dif = "Póliza en AXA no encontrada en base interna"
            tipo_pol_int = None

        conciliacion.append(ItemConciliacion(
            poliza=ind["poliza"],
            agente_codigo=ind["agente_codigo"],
            agente_nombre=ind["agente_nombre"],
            ramo=ind["ramo"],
            prima_primer_anio=ind["prima_primer_anio"],
            es_nueva_axa=bool(ind["es_nueva_axa"]),
            tipo_poliza_interna=tipo_pol_int,
            status=status,
            tipo_diferencia=dif,
        ))

    coincide_n = sum(1 for c in conciliacion if c.status == "COINCIDE")
    dif_n      = sum(1 for c in conciliacion if c.status == "DIFERENCIA")
    solo_axa_n = sum(1 for c in conciliacion if c.status == "SOLO_AXA")
    total_n    = len(conciliacion)
    pct = round((coincide_n / total_n * 100) if total_n else 0, 1)

    resumen = ResumenConciliacion(
        total=total_n, coincide=coincide_n, diferencia=dif_n,
        solo_axa=solo_axa_n, pct_coincidencia=pct
    )

    periodos_raw = db.execute(text("SELECT DISTINCT periodo FROM indicadores_axa ORDER BY periodo DESC")).scalars().all()

    return ConciliacionResponse(
        conciliacion=conciliacion,
        resumen=resumen,
        periodos=list(periodos_raw)
    )


# ═══════════════════════════════════════════════════════════════════
# IMPORTACIÓN — Excel de pólizas
# ═══════════════════════════════════════════════════════════════════
router_importacion = APIRouter(prefix="/importar", tags=["Importación"])


@router_importacion.post("/excel-polizas", response_model=ImportacionResult)
async def importar_excel_polizas(
    archivo: UploadFile = File(...),
    hoja: str = Query("querys", description="Nombre de la hoja a importar"),
    db: Session = Depends(get_db)
):
    """
    Importa pólizas desde un archivo Excel (POLIZAS01 o similar).
    Usa pandas para leer el archivo y aplica las reglas de negocio automáticamente.
    """
    if not archivo.filename.endswith((".xlsx", ".xls", ".xlsb")):
        raise HTTPException(400, "Solo se aceptan archivos Excel (.xlsx, .xls, .xlsb)")

    contenido = await archivo.read()
    errores = []
    nuevos = 0
    actualizados = 0

    try:
        df = pd.read_excel(io.BytesIO(contenido), sheet_name=hoja, dtype=str)
        df.columns = [c.strip().upper() for c in df.columns]
        df = df.where(pd.notna(df), None)

        # Mapeo de columnas Excel → modelo
        COL_MAP = {
            "POLIZA": "poliza_original",
            "ASEGURADO": "asegurado_nombre",
            "CONTRATANTE": "contratante_nombre",
            "RFC": "rfc",
            "FECINI": "fecha_inicio",
            "FECFIN": "fecha_fin",
            "FECEMI": "fecha_emision",
            "PRIMA_TOT": "prima_total",
            "PRIMANETA": "prima_neta",
            "IVA": "iva",
            "RECARGO": "recargo",
            "SUMA": "suma_asegurada",
            "DEDUCIBLE": "deducible",
            "COASEGURO": "coaseguro",
            "FP": "forma_pago",
            "TIPPAG": "tipo_pago",
            "STATUS": "status_recibo",
            "GAMA": "gama",
            "NOMRAMO": "ramo_nombre_raw",
            "MYSTATUS": "mystatus_raw",
            "ASEGS": "num_asegurados",
            "AGENTE": "agente_codigo_raw",
        }

        for i, row in df.iterrows():
            try:
                pol_num = row.get("POLIZA")
                if not pol_num:
                    continue

                # Buscar agente
                agente_codigo = row.get("AGENTE")
                agente_id = None
                if agente_codigo:
                    ag = db.execute(
                        text("SELECT id FROM agentes WHERE codigo_agente = :c"),
                        {"c": str(agente_codigo).strip()}
                    ).scalar()
                    agente_id = ag

                # Buscar producto
                ramo_raw = (row.get("NOMRAMO") or "").upper()
                gama = row.get("GAMA")
                plan = row.get("PLAN") or row.get("COBERTURA")
                ramo_codigo = 11 if "VIDA" in ramo_raw else 34

                prod = db.execute(text("""
                    SELECT id FROM productos
                    WHERE ramo_codigo = :rc
                    ORDER BY id LIMIT 1
                """), {"rc": ramo_codigo}).scalar()

                # Fechas
                fecha_ini = str(row.get("FECINI") or "")[:10] or None
                fecha_fin = str(row.get("FECFIN") or "")[:10] or None
                anio = int(fecha_ini[:4]) if fecha_ini and len(fecha_ini) >= 4 else None

                # Importes
                def to_float(v):
                    try: return float(str(v).replace(",", "").strip()) if v else None
                    except: return None

                prima_neta = to_float(row.get("PRIMANETA"))
                prima_total = to_float(row.get("PRIMA_TOT"))
                iva = to_float(row.get("IVA")) or 0
                recargo = to_float(row.get("RECARGO")) or 0
                suma = to_float(row.get("SUMA"))
                deducible = to_float(row.get("DEDUCIBLE"))

                # Status
                status = (row.get("STATUS") or "PAGADA").strip()
                mystatus = calcular_mystatus(status)

                # Verificar si ya existe
                existente = db.execute(
                    text("SELECT id FROM polizas WHERE poliza_original = :p"),
                    {"p": str(pol_num).strip()}
                ).scalar()

                if existente:
                    db.execute(text("""
                        UPDATE polizas SET
                            prima_neta = :pn, prima_total = :pt,
                            status_recibo = :sr, mystatus = :ms,
                            updated_at = datetime('now')
                        WHERE id = :id
                    """), {"pn": prima_neta, "pt": prima_total, "sr": status, "ms": mystatus, "id": existente})
                    actualizados += 1
                else:
                    db.execute(text("""
                        INSERT INTO polizas (
                            poliza_original, poliza_estandar, agente_id, producto_id,
                            asegurado_nombre, fecha_inicio, fecha_fin, fecha_emision,
                            prima_total, prima_neta, iva, recargo, suma_asegurada,
                            deducible, num_asegurados, forma_pago, tipo_pago,
                            status_recibo, gama, mystatus, periodo_aplicacion,
                            anio_aplicacion, fuente
                        ) VALUES (
                            :po, :pe, :ai, :pi,
                            :an, :fi, :ff, :fe,
                            :pt, :pn, :iv, :re, :su,
                            :de, :na, :fp, :tp,
                            :sr, :ga, :ms, :per,
                            :anio, 'EXCEL_IMPORT'
                        )
                    """), {
                        "po": str(pol_num).strip(),
                        "pe": normalizar_poliza(str(pol_num).strip()),
                        "ai": agente_id, "pi": prod,
                        "an": row.get("ASEGURADO"), "fi": fecha_ini,
                        "ff": fecha_fin, "fe": str(row.get("FECEMI") or "")[:10] or None,
                        "pt": prima_total, "pn": prima_neta, "iv": iva, "re": recargo,
                        "su": suma, "de": deducible,
                        "na": int(float(str(row.get("ASEGS") or 1))),
                        "fp": row.get("FP"), "tp": row.get("TIPPAG"),
                        "sr": status, "ga": gama, "ms": mystatus,
                        "per": f"{anio}-{fecha_ini[5:7]}" if fecha_ini and anio else None,
                        "anio": anio,
                    })
                    nuevos += 1

            except Exception as e:
                errores.append(f"Fila {i+2}: {str(e)}")
                continue

        db.commit()

        # Log de importación
        log = Importacion(
            tipo="EXCEL_POLIZAS",
            archivo_nombre=archivo.filename,
            registros_procesados=len(df),
            registros_nuevos=nuevos,
            registros_actualizados=actualizados,
            registros_error=len(errores),
            errores_detalle="\n".join(errores[:20]) if errores else None,
        )
        db.add(log)
        db.commit()

        return ImportacionResult(
            success=True,
            registros_procesados=len(df),
            registros_nuevos=nuevos,
            registros_actualizados=actualizados,
            registros_error=len(errores),
            errores=errores[:10],
            mensaje=f"Importación completada: {nuevos} nuevas, {actualizados} actualizadas, {len(errores)} errores"
        )

    except Exception as e:
        raise HTTPException(500, f"Error procesando archivo: {str(e)}")


@router_importacion.post("/indicadores-axa", response_model=ImportacionResult)
async def importar_indicadores_axa(
    archivo: UploadFile = File(...),
    periodo: str = Query(..., description="Periodo en formato YYYY-MM, ej: 2025-07"),
    hoja_detalle: str = Query("detalle_pol", description="Hoja con detalle de pólizas"),
    db: Session = Depends(get_db)
):
    """
    Importa indicadores AXA desde el Excel mensual.
    Lee la hoja 'detalle_pol' y ejecuta la conciliación automáticamente.
    """
    contenido = await archivo.read()
    errores = []
    nuevos = 0

    try:
        df = pd.read_excel(io.BytesIO(contenido), sheet_name=hoja_detalle, dtype=str)
        df.columns = [c.strip().upper() for c in df.columns]
        df = df.where(pd.notna(df), None)

        for i, row in df.iterrows():
            try:
                poliza = (row.get("POLIZA") or row.get("NUMERO_POLIZA") or "").strip()
                if not poliza:
                    continue

                def to_float(v):
                    try: return float(str(v).replace(",","").strip()) if v else None
                    except: return None

                # Buscar si la póliza existe en base interna
                encontrada = db.execute(
                    text("SELECT id FROM polizas WHERE poliza_estandar=:pe OR poliza_original=:po"),
                    {"pe": normalizar_poliza(poliza), "po": poliza}
                ).scalar()

                db.execute(text("""
                    INSERT INTO indicadores_axa (
                        periodo, fecha_recepcion, poliza, agente_codigo, ramo,
                        num_asegurados, polizas_equivalentes, prima_primer_anio,
                        es_nueva_axa, reconocimiento_antiguedad, encontrada_en_base
                    ) VALUES (:per, date('now'), :pol, :agc, :ram, :nas, :peq, :ppa, :ean, :rag, :enb)
                """), {
                    "per": periodo,
                    "pol": poliza,
                    "agc": (row.get("AGENTE") or row.get("CLAVE_AGENTE") or "").strip() or None,
                    "ram": (row.get("RAMO") or "").strip() or None,
                    "nas": int(float(row.get("NUM_ASEGURADOS") or 1)),
                    "peq": to_float(row.get("POLIZAS_EQUIVALENTES")),
                    "ppa": to_float(row.get("PRIMA_PRIMER_ANIO") or row.get("PRIMA")),
                    "ean": 1,  # AXA solo envía pólizas nuevas en detalle_pol
                    "rag": 1 if (row.get("ANTIGUEDAD_AXA") or "") else 0,
                    "enb": 1 if encontrada else 0,
                })
                nuevos += 1

            except Exception as e:
                errores.append(f"Fila {i+2}: {str(e)}")

        db.commit()

        log = Importacion(
            tipo="INDICADORES_AXA",
            archivo_nombre=archivo.filename,
            registros_procesados=len(df),
            registros_nuevos=nuevos,
            registros_error=len(errores),
            errores_detalle="\n".join(errores[:20]) if errores else None,
        )
        db.add(log)
        db.commit()

        return ImportacionResult(
            success=True,
            registros_procesados=len(df),
            registros_nuevos=nuevos,
            registros_error=len(errores),
            errores=errores[:10],
            mensaje=f"Indicadores AXA importados: {nuevos} registros para periodo {periodo}"
        )

    except Exception as e:
        raise HTTPException(500, f"Error procesando indicadores: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# EXPORTACIÓN — Excel
# ═══════════════════════════════════════════════════════════════════
router_exportacion = APIRouter(prefix="/exportar", tags=["Exportación"])


@router_exportacion.get("/polizas-excel")
def exportar_polizas_excel(
    anio: Optional[int] = None,
    ramo: Optional[str] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Exporta las pólizas filtradas como archivo Excel."""
    from fastapi.responses import StreamingResponse

    conditions = ["1=1"]
    params: dict = {}
    if anio:
        conditions.append("p.anio_aplicacion = :anio")
        params["anio"] = anio
    if ramo == "vida":
        conditions.append("pr.ramo_codigo = 11")
    elif ramo == "gmm":
        conditions.append("pr.ramo_codigo = 34")
    if tipo:
        conditions.append("p.tipo_poliza = :tipo")
        params["tipo"] = tipo.upper()

    where = " AND ".join(conditions)
    rows = db.execute(text(f"""
        SELECT p.poliza_original, p.asegurado_nombre, a.nombre_completo as agente,
               a.codigo_agente, pr.ramo_nombre, p.gama, p.fecha_inicio, p.fecha_fin,
               p.prima_neta, p.prima_total, p.iva, p.forma_pago, p.tipo_pago,
               p.status_recibo, p.tipo_poliza, p.tipo_prima, p.pct_comision,
               p.num_asegurados, p.suma_asegurada, p.mystatus, p.periodo_aplicacion
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE {where}
        ORDER BY p.fecha_inicio DESC
    """), params).mappings().all()

    df = pd.DataFrame([dict(r) for r in rows])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Pólizas", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Pólizas"]
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#1e3a5f", "font_color": "white", "border": 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
        worksheet.set_column(0, len(df.columns) - 1, 18)

    output.seek(0)
    filename = f"polizas_MAG_{anio or 'todos'}_{ramo or 'todos'}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
