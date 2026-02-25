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

from .database import (
    get_db, Agente, Poliza, Producto, IndicadorAxa, Meta, Importacion,
    Segmento, Recibo, Conciliacion, Presupuesto,
    Contratante, Solicitud, DistribucionComision, Configuracion,
)
from .schemas import (
    AgenteOut, AgenteCreate,
    PolizaOut, PolizaCreate, PolizaListResponse,
    DashboardResponse, KPIs, ProduccionMensual, TopAgente, DistribucionGama,
    ConciliacionResponse, ResumenConciliacion, ItemConciliacion,
    ImportacionResult,
    EjecutivoResponse, ComparativoRamo, ResumenSegmento, AgenteOperativo,
    ProduccionMensualComparativo,
    CobranzaResponse, CobranzaResumen, DeudorPrima, RenovacionPendiente,
    PolizaCancelada, AlertaCobranza, SeguimientoMensual,
    FinanzasResponse, ResumenFinanciero, IngresoEgresoMensual,
    ProyeccionCierre, PresupuestoMensualComp, TendenciaAnual,
    ContratanteOut, ContratanteCreate,
    SolicitudOut, SolicitudCreate, SolicitudUpdate, SolicitudesResponse, PipelineResumen,
    DistribucionOut, DistribucionCreate,
    ConfiguracionItem, ConfiguracionUpdate, ConfiguracionResponse,
)
from .rules import (
    normalizar_poliza, calcular_mystatus, es_reexpedicion, agrupar_segmento,
    clasificar_cy, aplicar_reglas_poliza, aplicar_reglas_batch
)

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


MESES_NOMBRE = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _var_pct(actual, anterior):
    """Calcula variación porcentual, retorna 0 si anterior es 0."""
    if not anterior:
        return 100.0 if actual else 0.0
    return round(((actual - anterior) / anterior) * 100, 2)


@router_dashboard.get("/ejecutivo", response_model=EjecutivoResponse)
def get_dashboard_ejecutivo(
    anio: int = Query(2025, description="Año actual de análisis"),
    segmento: Optional[str] = Query(None, description="Filtrar por segmento agrupado: ALFA, BETA, OMEGA"),
    gestion: Optional[str] = Query(None, description="Filtrar por gestión comercial"),
    agente_codigo: Optional[str] = Query(None, description="Filtrar por código de agente"),
    top_n: int = Query(0, description="Top N agentes (0 = todos)"),
    db: Session = Depends(get_db)
):
    """
    Dashboard Ejecutivo (Fase 1) — replica VISTAS.xlsx y VISTAS CUITLAHUAC.xlsx.
    Comparativo interanual, segmentos, y vista operativa por agente.
    """
    anio_ant = anio - 1

    # ── Filtros opcionales ──
    filtro_extra = ""
    params_extra = {}
    if segmento:
        filtro_extra += " AND a.segmento_agrupado = :seg"
        params_extra["seg"] = segmento.upper()
    if gestion:
        filtro_extra += " AND a.gestion_comercial LIKE :gest"
        params_extra["gest"] = f"%{gestion}%"
    if agente_codigo:
        filtro_extra += " AND a.codigo_agente = :agc"
        params_extra["agc"] = agente_codigo

    # ── Datos del año actual y anterior ──
    for yr_key, yr_val in [("act", anio), ("ant", anio_ant)]:
        params_extra[f"anio_{yr_key}"] = yr_val

    polizas_query = text(f"""
        SELECT p.*, pr.ramo_codigo, pr.ramo_nombre,
               a.codigo_agente, a.nombre_completo as agente_nombre,
               a.segmento_nombre, a.segmento_agrupado, a.gestion_comercial,
               a.situacion, a.estado as agente_estado
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.anio_aplicacion IN (:anio_act, :anio_ant) {filtro_extra}
    """)
    all_polizas = db.execute(polizas_query, params_extra).mappings().all()

    # Separar por año
    pol_act = [p for p in all_polizas if p["anio_aplicacion"] == anio]
    pol_ant = [p for p in all_polizas if p["anio_aplicacion"] == anio_ant]

    # ── 1. COMPARATIVO POR RAMO ──
    def build_comparativo(ramo_nombre, ramo_codigo, p_act, p_ant):
        act_nuevas = [p for p in p_act if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "NUEVA"]
        ant_nuevas = [p for p in p_ant if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "NUEVA"]
        act_subs = [p for p in p_act if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "SUBSECUENTE"]
        ant_subs = [p for p in p_ant if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "SUBSECUENTE"]

        pol_act_n = len(act_nuevas)
        pol_ant_n = len(ant_nuevas)
        aseg_act = sum(p["num_asegurados"] or 1 for p in act_nuevas)
        aseg_ant = sum(p["num_asegurados"] or 1 for p in ant_nuevas)
        eq_act = sum(p["equivalencias_emitidas"] or 0 for p in act_nuevas)
        eq_ant = sum(p["equivalencias_emitidas"] or 0 for p in ant_nuevas)
        pn_act = sum(p["prima_neta"] or 0 for p in act_nuevas)
        pn_ant = sum(p["prima_neta"] or 0 for p in ant_nuevas)
        ps_act = sum(p["prima_neta"] or 0 for p in act_subs)
        ps_ant = sum(p["prima_neta"] or 0 for p in ant_subs)
        pt_act = pn_act + ps_act
        pt_ant = pn_ant + ps_ant

        return ComparativoRamo(
            ramo=ramo_nombre,
            polizas_anterior=pol_ant_n, polizas_actual=pol_act_n,
            polizas_variacion=_var_pct(pol_act_n, pol_ant_n),
            asegurados_anterior=aseg_ant, asegurados_actual=aseg_act,
            asegurados_variacion=_var_pct(aseg_act, aseg_ant),
            equivalentes_anterior=round(eq_ant, 1), equivalentes_actual=round(eq_act, 1),
            equivalentes_variacion=_var_pct(eq_act, eq_ant),
            prima_nueva_anterior=round(pn_ant, 2), prima_nueva_actual=round(pn_act, 2),
            prima_nueva_variacion=_var_pct(pn_act, pn_ant),
            prima_subsecuente_anterior=round(ps_ant, 2), prima_subsecuente_actual=round(ps_act, 2),
            prima_subsecuente_variacion=_var_pct(ps_act, ps_ant),
            prima_total_anterior=round(pt_ant, 2), prima_total_actual=round(pt_act, 2),
            prima_total_variacion=_var_pct(pt_act, pt_ant),
        )

    comp_gmm = build_comparativo("GMM", 34, pol_act, pol_ant)
    comp_vida = build_comparativo("VIDA", 11, pol_act, pol_ant)

    # ── 2. RESUMEN POR SEGMENTO ──
    seg_data = defaultdict(lambda: {
        "agentes": set(), "polizas_vida": 0, "polizas_gmm": 0,
        "prima_vida": 0.0, "prima_gmm": 0.0, "equivalentes": 0.0,
    })
    for p in pol_act:
        seg = p["segmento_agrupado"] or "SIN SEGMENTO"
        ag_code = p["codigo_agente"]
        seg_data[seg]["agentes"].add(ag_code)
        if p["ramo_codigo"] == 11 and p["tipo_poliza"] == "NUEVA":
            seg_data[seg]["polizas_vida"] += 1
            seg_data[seg]["prima_vida"] += (p["prima_neta"] or 0)
            seg_data[seg]["equivalentes"] += (p["equivalencias_emitidas"] or 0)
        elif p["ramo_codigo"] == 34 and p["tipo_poliza"] == "NUEVA":
            seg_data[seg]["polizas_gmm"] += 1
            seg_data[seg]["prima_gmm"] += (p["prima_neta"] or 0)

    segmentos_res = []
    for seg_name in ["ALFA", "BETA", "OMEGA", "SIN SEGMENTO"]:
        if seg_name in seg_data:
            d = seg_data[seg_name]
            segmentos_res.append(ResumenSegmento(
                segmento=seg_name,
                num_agentes=len(d["agentes"]),
                polizas_vida=d["polizas_vida"],
                polizas_gmm=d["polizas_gmm"],
                prima_vida=round(d["prima_vida"], 2),
                prima_gmm=round(d["prima_gmm"], 2),
                prima_total=round(d["prima_vida"] + d["prima_gmm"], 2),
                equivalentes=round(d["equivalentes"], 1),
            ))

    # ── 3. VISTA OPERATIVA POR AGENTE ──
    agentes_map = defaultdict(lambda: {
        "clave": "", "nombre": "", "segmento": "", "segmento_agrupado": "",
        "gestion": "", "estado": "",
        # Actual
        "polizas_vida": 0, "equiv_vida": 0.0, "prima_pagada_vida": 0.0,
        "polizas_gmm": 0, "asegurados_gmm": 0, "prima_pagada_gmm": 0.0,
        # Anterior GMM
        "gmm_polizas_ant": 0, "gmm_prima_nueva_ant": 0.0, "gmm_prima_sub_ant": 0.0,
        # Actual GMM
        "gmm_polizas_act": 0, "gmm_prima_nueva_act": 0.0, "gmm_prima_sub_act": 0.0,
        # Anterior Vida
        "vida_polizas_ant": 0, "vida_equiv_ant": 0.0,
        "vida_prima_nueva_ant": 0.0, "vida_prima_sub_ant": 0.0,
        # Actual Vida
        "vida_polizas_act": 0, "vida_equiv_act": 0.0,
        "vida_prima_nueva_act": 0.0, "vida_prima_sub_act": 0.0,
    })

    for p in all_polizas:
        ag_code = p["codigo_agente"] or "SIN_AGENTE"
        a = agentes_map[ag_code]
        a["clave"] = ag_code
        a["nombre"] = p["agente_nombre"] or ""
        a["segmento"] = p["segmento_nombre"] or ""
        a["segmento_agrupado"] = p["segmento_agrupado"] or ""
        a["gestion"] = p["gestion_comercial"] or ""
        a["estado"] = p["agente_estado"] or p["situacion"] or ""

        is_act = p["anio_aplicacion"] == anio
        is_ant = p["anio_aplicacion"] == anio_ant
        is_vida = p["ramo_codigo"] == 11
        is_gmm = p["ramo_codigo"] == 34
        is_nueva = p["tipo_poliza"] == "NUEVA"
        is_sub = p["tipo_poliza"] == "SUBSECUENTE"
        prima = p["prima_neta"] or 0
        equiv = p["equivalencias_emitidas"] or 0

        if is_act and is_vida and is_nueva:
            a["polizas_vida"] += 1
            a["equiv_vida"] += equiv
            a["prima_pagada_vida"] += prima
            a["vida_polizas_act"] += 1
            a["vida_equiv_act"] += equiv
            a["vida_prima_nueva_act"] += prima
        elif is_act and is_vida and is_sub:
            a["vida_prima_sub_act"] += prima
        elif is_act and is_gmm and is_nueva:
            a["polizas_gmm"] += 1
            a["asegurados_gmm"] += (p["num_asegurados"] or 1)
            a["prima_pagada_gmm"] += prima
            a["gmm_polizas_act"] += 1
            a["gmm_prima_nueva_act"] += prima
        elif is_act and is_gmm and is_sub:
            a["gmm_prima_sub_act"] += prima
        elif is_ant and is_vida and is_nueva:
            a["vida_polizas_ant"] += 1
            a["vida_equiv_ant"] += equiv
            a["vida_prima_nueva_ant"] += prima
        elif is_ant and is_vida and is_sub:
            a["vida_prima_sub_ant"] += prima
        elif is_ant and is_gmm and is_nueva:
            a["gmm_polizas_ant"] += 1
            a["gmm_prima_nueva_ant"] += prima
        elif is_ant and is_gmm and is_sub:
            a["gmm_prima_sub_ant"] += prima

    # Buscar metas por agente
    metas_raw = db.execute(text("""
        SELECT m.*, a.codigo_agente
        FROM metas m
        LEFT JOIN agentes a ON m.agente_id = a.id
        WHERE m.anio = :anio AND m.periodo IS NULL
    """), {"anio": anio}).mappings().all()
    metas_by_agente = {m["codigo_agente"]: m for m in metas_raw if m["codigo_agente"]}
    meta_global = db.execute(
        text("SELECT * FROM metas WHERE anio=:a AND periodo IS NULL AND agente_id IS NULL"),
        {"a": anio}
    ).mappings().first()

    agentes_operativo = []
    for _, a in sorted(agentes_map.items(), key=lambda x: x[1]["prima_pagada_vida"] + x[1]["prima_pagada_gmm"], reverse=True):
        prima_total = a["prima_pagada_vida"] + a["prima_pagada_gmm"]
        gmm_total_ant = a["gmm_prima_nueva_ant"] + a["gmm_prima_sub_ant"]
        gmm_total_act = a["gmm_prima_nueva_act"] + a["gmm_prima_sub_act"]
        vida_total_ant = a["vida_prima_nueva_ant"] + a["vida_prima_sub_ant"]
        vida_total_act = a["vida_prima_nueva_act"] + a["vida_prima_sub_act"]

        # Metas
        meta = metas_by_agente.get(a["clave"])
        meta_pol = (meta["meta_polizas_vida"] or 0) if meta else 0
        meta_eq = 0
        meta_pv = (meta["meta_prima_vida"] or 0) if meta else 0
        meta_pg = (meta["meta_prima_gmm"] or 0) if meta else 0

        agentes_operativo.append(AgenteOperativo(
            clave=a["clave"], nombre=a["nombre"],
            segmento=a["segmento"], segmento_agrupado=a["segmento_agrupado"],
            gestion=a["gestion"], estado=a["estado"],
            polizas_vida=a["polizas_vida"], equiv_vida=round(a["equiv_vida"], 1),
            prima_pagada_vida=round(a["prima_pagada_vida"], 2),
            polizas_gmm=a["polizas_gmm"], asegurados_gmm=a["asegurados_gmm"],
            prima_pagada_gmm=round(a["prima_pagada_gmm"], 2),
            prima_pagada_total=round(prima_total, 2),
            meta_polizas=meta_pol, meta_equiv=meta_eq,
            faltante_polizas=max(0, meta_pol - a["polizas_vida"]),
            meta_prima_vida=meta_pv, falta_prima_vida=max(0, meta_pv - a["prima_pagada_vida"]),
            meta_prima_gmm=meta_pg, falta_prima_gmm=max(0, meta_pg - a["prima_pagada_gmm"]),
            gmm_polizas_ant=a["gmm_polizas_ant"], gmm_polizas_act=a["gmm_polizas_act"],
            gmm_prima_nueva_ant=round(a["gmm_prima_nueva_ant"], 2),
            gmm_prima_nueva_act=round(a["gmm_prima_nueva_act"], 2),
            gmm_prima_sub_ant=round(a["gmm_prima_sub_ant"], 2),
            gmm_prima_sub_act=round(a["gmm_prima_sub_act"], 2),
            gmm_total_ant=round(gmm_total_ant, 2), gmm_total_act=round(gmm_total_act, 2),
            gmm_crecimiento=_var_pct(gmm_total_act, gmm_total_ant),
            vida_polizas_ant=a["vida_polizas_ant"], vida_polizas_act=a["vida_polizas_act"],
            vida_equiv_ant=round(a["vida_equiv_ant"], 1), vida_equiv_act=round(a["vida_equiv_act"], 1),
            vida_prima_nueva_ant=round(a["vida_prima_nueva_ant"], 2),
            vida_prima_nueva_act=round(a["vida_prima_nueva_act"], 2),
            vida_prima_sub_ant=round(a["vida_prima_sub_ant"], 2),
            vida_prima_sub_act=round(a["vida_prima_sub_act"], 2),
            vida_total_ant=round(vida_total_ant, 2), vida_total_act=round(vida_total_act, 2),
            vida_crecimiento=_var_pct(vida_total_act, vida_total_ant),
        ))

    if top_n > 0:
        agentes_operativo = agentes_operativo[:top_n]

    # ── 4. PRODUCCIÓN MENSUAL COMPARATIVA ──
    def build_mensual_comp(ramo_codigo, p_act, p_ant):
        act_by_month = defaultdict(lambda: {"polizas": 0, "prima": 0.0})
        ant_by_month = defaultdict(lambda: {"polizas": 0, "prima": 0.0})
        for p in p_act:
            if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "NUEVA":
                per = p["periodo_aplicacion"] or ""
                if len(per) >= 7:
                    m = int(per[5:7])
                    act_by_month[m]["polizas"] += 1
                    act_by_month[m]["prima"] += (p["prima_neta"] or 0)
        for p in p_ant:
            if p["ramo_codigo"] == ramo_codigo and p["tipo_poliza"] == "NUEVA":
                per = p["periodo_aplicacion"] or ""
                if len(per) >= 7:
                    m = int(per[5:7])
                    ant_by_month[m]["polizas"] += 1
                    ant_by_month[m]["prima"] += (p["prima_neta"] or 0)

        result = []
        for m in range(1, 13):
            result.append(ProduccionMensualComparativo(
                mes=MESES_NOMBRE.get(m, str(m)), mes_num=m,
                polizas_anterior=ant_by_month[m]["polizas"],
                polizas_actual=act_by_month[m]["polizas"],
                prima_anterior=round(ant_by_month[m]["prima"], 2),
                prima_actual=round(act_by_month[m]["prima"], 2),
            ))
        return result

    mensual_gmm = build_mensual_comp(34, pol_act, pol_ant)
    mensual_vida = build_mensual_comp(11, pol_act, pol_ant)

    # ── Filtros disponibles ──
    segmentos_db = db.execute(text("SELECT DISTINCT segmento_agrupado FROM agentes WHERE segmento_agrupado IS NOT NULL")).scalars().all()
    gestiones_db = db.execute(text("SELECT DISTINCT gestion_comercial FROM agentes WHERE gestion_comercial IS NOT NULL")).scalars().all()

    return EjecutivoResponse(
        comparativo_gmm=comp_gmm,
        comparativo_vida=comp_vida,
        segmentos=segmentos_res,
        agentes_operativo=agentes_operativo,
        mensual_gmm=mensual_gmm,
        mensual_vida=mensual_vida,
        anio_actual=anio,
        anio_anterior=anio_ant,
        filtros_disponibles={
            "segmentos": list(segmentos_db),
            "gestiones": list(gestiones_db),
            "anios": [2022, 2023, 2024, 2025, 2026],
        }
    )


# ═══════════════════════════════════════════════════════════════════
# COBRANZA / DEUDOR POR PRIMA (Fase 2)
# ═══════════════════════════════════════════════════════════════════
router_cobranza = APIRouter(prefix="/cobranza", tags=["Cobranza"])

MESES_COMPLETOS = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _calcular_prioridad(dias_vencimiento, mystatus):
    """Calcula el semáforo de prioridad del deudor por prima."""
    ms = (mystatus or "").upper()
    if "PAGADA" in ms or "AL CORRIENTE" in ms:
        return "pagado"
    if "CANCELADA" in ms or "CANC" in ms:
        return "critico"
    if dias_vencimiento > 30:
        return "critico"       # 🔴 Vencido > 30 días
    if dias_vencimiento > 15:
        return "urgente"       # 🟠 15-30 días
    if dias_vencimiento > 0:
        return "atencion"      # 🟡 0-15 días
    return "al_dia"            # 🟢 Al día


@router_cobranza.get("", response_model=CobranzaResponse)
def get_cobranza(
    anio: int = Query(2025, description="Año de análisis"),
    ramo: Optional[str] = Query(None, description="Filtrar por ramo: vida, gmm"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad: critico, urgente, atencion, al_dia, pagado"),
    agente_codigo: Optional[str] = Query(None, description="Filtrar por código de agente"),
    db: Session = Depends(get_db)
):
    """
    Módulo de Cobranza y Deudor por Prima (Fase 2).
    Vista de priorización visual con semáforo de urgencia.
    """
    from datetime import datetime, timedelta

    hoy = datetime.now()
    hoy_str = hoy.strftime("%Y-%m-%d")

    # ── Filtros ──
    filtro_ramo = ""
    if ramo == "vida":
        filtro_ramo = " AND pr.ramo_codigo = 11"
    elif ramo == "gmm":
        filtro_ramo = " AND pr.ramo_codigo = 34"

    filtro_agente = ""
    params = {"anio": anio}
    if agente_codigo:
        filtro_agente = " AND a.codigo_agente = :agc"
        params["agc"] = agente_codigo

    # ── 1. DEUDOR POR PRIMA ──
    rows = db.execute(text(f"""
        SELECT p.*, pr.ramo_codigo, pr.ramo_nombre, pr.plan as producto_plan,
               a.codigo_agente, a.nombre_completo as agente_nombre,
               a.segmento_nombre
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.anio_aplicacion = :anio {filtro_ramo} {filtro_agente}
        ORDER BY p.fecha_inicio DESC
    """), params).mappings().all()

    deudores = []
    for p in rows:
        prima_neta = p["prima_neta"] or 0
        prima_total = p["prima_total"] or prima_neta
        prima_acum = p["prima_acumulada_basica"] or p["neta_acumulada"] or 0
        prima_pendiente = max(0, prima_neta - prima_acum)
        mystatus = p["mystatus"] or ""

        # Calcular días de vencimiento
        fecha_fin = p["fecha_fin"] or ""
        fecha_inicio = p["fecha_inicio"] or ""
        dias_venc = 0

        # Heurística: calcular próximo recibo basado en forma de pago
        fp = (p["forma_pago"] or "ANUAL").upper()
        meses_fp = 12
        if "SEMEST" in fp: meses_fp = 6
        elif "TRIM" in fp: meses_fp = 3
        elif "MENS" in fp: meses_fp = 1
        elif "BIMEST" in fp: meses_fp = 2

        # Calcular cuántos recibos debería tener y cuántos ha pagado
        recibo_actual = "-"
        fecha_prox = None
        if fecha_inicio and len(fecha_inicio) >= 10:
            try:
                fi = datetime.strptime(fecha_inicio[:10], "%Y-%m-%d")
                meses_desde_inicio = max(0, (hoy.year - fi.year) * 12 + hoy.month - fi.month)
                recibos_esperados = min(12 // meses_fp, max(1, meses_desde_inicio // meses_fp + 1))
                total_recibos = 12 // meses_fp
                recibo_actual = f"{min(recibos_esperados, total_recibos)}/{total_recibos}"

                # Fecha próximo recibo
                proximo = fi + timedelta(days=meses_fp * 30 * recibos_esperados)
                fecha_prox = proximo.strftime("%Y-%m-%d")

                # Días de vencimiento (positivo = vencido)
                if prima_acum < prima_neta and prima_acum > 0:
                    dias_venc = max(0, (hoy - proximo).days)
                elif prima_acum == 0 and "PAGADA" not in mystatus.upper() and "AL CORRIENTE" not in mystatus.upper():
                    dias_venc = max(0, (hoy - fi - timedelta(days=30)).days)
            except (ValueError, TypeError):
                pass

        prio = _calcular_prioridad(dias_venc, mystatus)

        # Filtrar por prioridad si se solicita
        if prioridad and prio != prioridad:
            continue

        deudores.append(DeudorPrima(
            poliza=p["poliza_original"],
            contratante=p["contratante_nombre"],
            asegurado=p["asegurado_nombre"],
            agente_clave=p["codigo_agente"],
            agente_nombre=p["agente_nombre"],
            ramo=p["ramo_nombre"],
            plan=p["producto_plan"],
            gama=p["gama"],
            segmento=p["segmento_nombre"],
            prima_neta=round(prima_neta, 2),
            prima_total=round(prima_total, 2),
            prima_acumulada=round(prima_acum, 2),
            prima_pendiente=round(prima_pendiente, 2),
            fecha_inicio=fecha_inicio,
            fecha_fin=p["fecha_fin"],
            fecha_proximo_recibo=fecha_prox,
            status=p["status_recibo"],
            mystatus=mystatus,
            dias_vencimiento=dias_venc,
            prioridad=prio,
            recibo_actual=recibo_actual,
            moneda=p["moneda"],
        ))

    # Ordenar por prioridad: critico > urgente > atencion > al_dia > pagado
    orden_prio = {"critico": 0, "urgente": 1, "atencion": 2, "al_dia": 3, "pagado": 4}
    deudores.sort(key=lambda d: (orden_prio.get(d.prioridad, 5), -d.dias_vencimiento))

    # ── 2. RESUMEN ──
    criticas = sum(1 for d in deudores if d.prioridad == "critico")
    urgentes = sum(1 for d in deudores if d.prioridad == "urgente")
    atencion = sum(1 for d in deudores if d.prioridad == "atencion")
    al_dia = sum(1 for d in deudores if d.prioridad == "al_dia")
    pagadas = sum(1 for d in deudores if d.prioridad == "pagado")
    prima_por_cobrar = sum(d.prima_pendiente for d in deudores)
    prima_cobrada = sum(d.prima_acumulada for d in deudores)
    total_prima = prima_por_cobrar + prima_cobrada

    resumen = CobranzaResumen(
        total_polizas=len(deudores),
        criticas=criticas,
        urgentes=urgentes,
        atencion=atencion,
        al_dia=al_dia,
        pagadas=pagadas,
        prima_por_cobrar=round(prima_por_cobrar, 2),
        prima_cobrada=round(prima_cobrada, 2),
        pct_cobranza=round((prima_cobrada / total_prima * 100) if total_prima > 0 else 0, 1),
    )

    # ── 3. RENOVACIONES PENDIENTES ──
    renovaciones_raw = db.execute(text(f"""
        SELECT p.poliza_original, p.contratante_nombre, p.fecha_fin, p.prima_neta,
               p.status_recibo, p.mystatus,
               pr.ramo_nombre, a.codigo_agente, a.nombre_completo as agente_nombre
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.fecha_fin IS NOT NULL AND p.fecha_fin != ''
          AND p.fecha_fin >= :hoy_m60 AND p.fecha_fin <= :hoy_p90
          {filtro_ramo} {filtro_agente}
        ORDER BY p.fecha_fin ASC
    """), {**params, "hoy_m60": (hoy - timedelta(days=60)).strftime("%Y-%m-%d"),
           "hoy_p90": (hoy + timedelta(days=90)).strftime("%Y-%m-%d")}).mappings().all()

    renovaciones = []
    for r in renovaciones_raw:
        fecha_fin = r["fecha_fin"] or ""
        dias_ren = 0
        estado_ren = "por_vencer"
        if fecha_fin and len(fecha_fin) >= 10:
            try:
                ff = datetime.strptime(fecha_fin[:10], "%Y-%m-%d")
                dias_ren = (ff - hoy).days
                if dias_ren < 0:
                    estado_ren = "vencida"
                elif dias_ren <= 30:
                    estado_ren = "por_vencer"
                else:
                    estado_ren = "por_vencer"
            except ValueError:
                pass

        ms = (r["mystatus"] or "").upper()
        if "PAGADA" in ms or "AL CORRIENTE" in ms or "REHABILITADA" in ms:
            estado_ren = "renovada"

        renovaciones.append(RenovacionPendiente(
            poliza=r["poliza_original"],
            contratante=r["contratante_nombre"],
            agente_nombre=r["agente_nombre"],
            agente_clave=r["codigo_agente"],
            ramo=r["ramo_nombre"],
            prima_neta=round(r["prima_neta"] or 0, 2),
            fecha_fin=fecha_fin,
            dias_para_renovar=dias_ren,
            status=r["status_recibo"],
            estado_renovacion=estado_ren,
        ))

    # ── 4. PÓLIZAS CANCELADAS ──
    canceladas_raw = db.execute(text(f"""
        SELECT p.poliza_original, p.contratante_nombre, p.prima_neta,
               p.prima_acumulada_basica, p.neta_acumulada, p.fecha_inicio,
               p.mystatus, p.estatus_detalle,
               pr.ramo_nombre, a.codigo_agente, a.nombre_completo as agente_nombre
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        LEFT JOIN agentes a ON p.agente_id = a.id
        WHERE p.anio_aplicacion = :anio
          AND (p.mystatus LIKE '%CANCELADA%' OR p.mystatus LIKE '%CANC%'
               OR p.flag_cancelada = 0)
          {filtro_ramo} {filtro_agente}
        ORDER BY p.prima_neta DESC
    """), params).mappings().all()

    canceladas = []
    for c in canceladas_raw:
        prima_n = c["prima_neta"] or 0
        prima_a = c["prima_acumulada_basica"] or c["neta_acumulada"] or 0
        canceladas.append(PolizaCancelada(
            poliza=c["poliza_original"],
            contratante=c["contratante_nombre"],
            agente_nombre=c["agente_nombre"],
            agente_clave=c["codigo_agente"],
            ramo=c["ramo_nombre"],
            prima_neta=round(prima_n, 2),
            prima_acumulada=round(prima_a, 2),
            prima_perdida=round(max(0, prima_n - prima_a), 2),
            fecha_inicio=c["fecha_inicio"],
            mystatus=c["mystatus"],
            motivo=c["estatus_detalle"] or c["mystatus"],
            estatus_detalle=c["estatus_detalle"],
        ))

    # ── 5. ALERTAS ──
    alertas = []
    if criticas > 0:
        top_criticas = [d for d in deudores if d.prioridad == "critico"][:3]
        alertas.append(AlertaCobranza(
            tipo="vencido", icono="🔴",
            titulo=f"{criticas} póliza{'s' if criticas > 1 else ''} en estado CRÍTICO",
            descripcion=f"Recibos vencidos por más de 30 días. Prima en riesgo: {round(sum(d.prima_pendiente for d in top_criticas), 2):,.0f} MXN",
            dias=max((d.dias_vencimiento for d in top_criticas), default=0),
            monto=sum(d.prima_pendiente for d in top_criticas),
        ))

    if urgentes > 0:
        alertas.append(AlertaCobranza(
            tipo="por_cancelar", icono="🟠",
            titulo=f"{urgentes} póliza{'s' if urgentes > 1 else ''} URGENTES",
            descripcion=f"Recibos vencidos entre 15-30 días. Cobrar antes de que se cancelen.",
            monto=sum(d.prima_pendiente for d in deudores if d.prioridad == "urgente"),
        ))

    ren_por_vencer = [r for r in renovaciones if r.estado_renovacion == "por_vencer" and r.dias_para_renovar <= 30]
    if len(ren_por_vencer) > 0:
        alertas.append(AlertaCobranza(
            tipo="renovacion", icono="🔄",
            titulo=f"{len(ren_por_vencer)} renovación(es) en los próximos 30 días",
            descripcion=f"Prima de renovación: {round(sum(r.prima_neta for r in ren_por_vencer), 2):,.0f} MXN",
            monto=sum(r.prima_neta for r in ren_por_vencer),
        ))

    if len(canceladas) > 0:
        prima_perdida_total = sum(c.prima_perdida for c in canceladas)
        alertas.append(AlertaCobranza(
            tipo="cancelada", icono="⚠️",
            titulo=f"{len(canceladas)} póliza{'s' if len(canceladas) > 1 else ''} cancelada{'s' if len(canceladas) > 1 else ''}",
            descripcion=f"Prima perdida acumulada: ${prima_perdida_total:,.0f} MXN",
            monto=prima_perdida_total,
        ))

    # ── 6. SEGUIMIENTO MENSUAL DE COBRANZA ──
    seguimiento = []
    for m in range(1, 13):
        per = f"{anio}-{m:02d}"
        pols_mes = [d for d in deudores if (d.fecha_inicio or "")[:7] == per]
        cobrado = sum(d.prima_acumulada for d in pols_mes)
        total = sum(d.prima_neta for d in pols_mes)
        seguimiento.append(SeguimientoMensual(
            mes=MESES_COMPLETOS.get(m, str(m)),
            mes_num=m,
            meta=round(total, 2),
            cobrado=round(cobrado, 2),
            pct=round((cobrado / total * 100) if total > 0 else 0, 1),
            polizas=len(pols_mes),
        ))

    # ── Filtros disponibles ──
    ramos_db = db.execute(text("SELECT DISTINCT ramo_nombre FROM productos WHERE ramo_nombre IS NOT NULL")).scalars().all()

    return CobranzaResponse(
        resumen=resumen,
        deudores=deudores,
        renovaciones=renovaciones,
        canceladas=canceladas,
        alertas=alertas,
        seguimiento_mensual=seguimiento,
        filtros_disponibles={
            "ramos": list(ramos_db),
            "prioridades": ["critico", "urgente", "atencion", "al_dia", "pagado"],
            "anios": [2022, 2023, 2024, 2025, 2026],
        }
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
                moneda = (row.get("MON") or "MN").strip()

                # ── Aplicar reglas de cálculo (columnas AUTOMATICO) ──
                poliza_dict = {
                    "poliza_original": str(pol_num).strip(),
                    "fecha_inicio": fecha_ini,
                    "prima_neta": prima_neta,
                    "moneda": moneda,
                    "mystatus": mystatus,
                    "status_recibo": status,
                    "anio_aplicacion": anio,
                    "es_nueva": None,
                }
                reglas = aplicar_reglas_poliza(poliza_dict, ramo_codigo=ramo_codigo)

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
                            moneda = :mon,
                            largo_poliza = :largo, raiz_poliza_6 = :raiz6,
                            terminacion = :term, id_compuesto = :id_comp,
                            es_reexpedicion = :reexp, primer_anio = :primer,
                            fecha_aplicacion = :fec_apli, mes_aplicacion = :mes_apli,
                            pendientes_pago = :pend, trimestre = :trim,
                            flag_pagada = :fpag, flag_nueva_formal = :fnueva,
                            prima_anual_pesos = :pap, equivalencias_emitidas = :eqe,
                            equivalencias_pagadas = :eqp, flag_cancelada = :fcanc,
                            prima_proporcional = :pprop, condicional_prima = :cprim,
                            prima_acumulada_basica = :pacum,
                            updated_at = datetime('now')
                        WHERE id = :id
                    """), {
                        "pn": prima_neta, "pt": prima_total, "sr": status,
                        "ms": mystatus, "mon": moneda, "id": existente,
                        "largo": reglas["largo_poliza"], "raiz6": reglas["raiz_poliza_6"],
                        "term": reglas["terminacion"], "id_comp": reglas["id_compuesto"],
                        "reexp": reglas["es_reexpedicion"], "primer": reglas["primer_anio"],
                        "fec_apli": reglas["fecha_aplicacion"], "mes_apli": reglas["mes_aplicacion"],
                        "pend": reglas["pendientes_pago"], "trim": reglas["trimestre"],
                        "fpag": reglas["flag_pagada"], "fnueva": reglas["flag_nueva_formal"],
                        "pap": reglas["prima_anual_pesos"], "eqe": reglas["equivalencias_emitidas"],
                        "eqp": reglas["equivalencias_pagadas"], "fcanc": reglas["flag_cancelada"],
                        "pprop": reglas["prima_proporcional"], "cprim": reglas["condicional_prima"],
                        "pacum": reglas["prima_acumulada_basica"],
                    })
                    actualizados += 1
                else:
                    db.execute(text("""
                        INSERT INTO polizas (
                            poliza_original, poliza_estandar, agente_id, producto_id,
                            asegurado_nombre, fecha_inicio, fecha_fin, fecha_emision,
                            prima_total, prima_neta, iva, recargo, suma_asegurada,
                            deducible, num_asegurados, forma_pago, tipo_pago,
                            status_recibo, gama, mystatus, periodo_aplicacion,
                            anio_aplicacion, moneda, fuente,
                            largo_poliza, raiz_poliza_6, terminacion, id_compuesto,
                            es_reexpedicion, primer_anio, fecha_aplicacion,
                            mes_aplicacion, pendientes_pago, trimestre,
                            flag_pagada, flag_nueva_formal, prima_anual_pesos,
                            equivalencias_emitidas, equivalencias_pagadas,
                            flag_cancelada, prima_proporcional, condicional_prima,
                            prima_acumulada_basica
                        ) VALUES (
                            :po, :pe, :ai, :pi,
                            :an, :fi, :ff, :fe,
                            :pt, :pn, :iv, :re, :su,
                            :de, :na, :fp, :tp,
                            :sr, :ga, :ms, :per,
                            :anio, :mon, 'EXCEL_IMPORT',
                            :largo, :raiz6, :term, :id_comp,
                            :reexp, :primer, :fec_apli,
                            :mes_apli, :pend, :trim,
                            :fpag, :fnueva, :pap,
                            :eqe, :eqp,
                            :fcanc, :pprop, :cprim,
                            :pacum
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
                        "anio": anio, "mon": moneda,
                        "largo": reglas["largo_poliza"], "raiz6": reglas["raiz_poliza_6"],
                        "term": reglas["terminacion"], "id_comp": reglas["id_compuesto"],
                        "reexp": reglas["es_reexpedicion"], "primer": reglas["primer_anio"],
                        "fec_apli": reglas["fecha_aplicacion"], "mes_apli": reglas["mes_aplicacion"],
                        "pend": reglas["pendientes_pago"], "trim": reglas["trimestre"],
                        "fpag": reglas["flag_pagada"], "fnueva": reglas["flag_nueva_formal"],
                        "pap": reglas["prima_anual_pesos"], "eqe": reglas["equivalencias_emitidas"],
                        "eqp": reglas["equivalencias_pagadas"], "fcanc": reglas["flag_cancelada"],
                        "pprop": reglas["prima_proporcional"], "cprim": reglas["condicional_prima"],
                        "pacum": reglas["prima_acumulada_basica"],
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


@router_importacion.post("/aplicar-reglas", response_model=ImportacionResult)
def aplicar_reglas_todas(
    anio: Optional[int] = Query(None, description="Año a recalcular (None = todos)"),
    ramo: Optional[str] = Query(None, description="Ramo: vida, gmm, o None = todos"),
    db: Session = Depends(get_db)
):
    """
    Recalcula todas las columnas derivadas (reglas del AUTOMATICO)
    sobre las pólizas existentes en la BD.
    Útil después de cambiar reglas o actualizar datos de referencia.
    """
    conditions = ["1=1"]
    params: dict = {}
    if anio:
        conditions.append("p.anio_aplicacion = :anio")
        params["anio"] = anio
    if ramo == "vida":
        conditions.append("pr.ramo_codigo = 11")
    elif ramo == "gmm":
        conditions.append("pr.ramo_codigo = 34")

    where = " AND ".join(conditions)
    rows = db.execute(text(f"""
        SELECT p.*, pr.ramo_codigo, pr.ramo_nombre
        FROM polizas p
        LEFT JOIN productos pr ON p.producto_id = pr.id
        WHERE {where}
    """), params).mappings().all()

    polizas_dicts = [dict(r) for r in rows]
    if not polizas_dicts:
        return ImportacionResult(
            success=True, registros_procesados=0, registros_nuevos=0,
            registros_actualizados=0, registros_error=0, errores=[],
            mensaje="No se encontraron pólizas para recalcular"
        )

    resultados = aplicar_reglas_batch(polizas_dicts)
    actualizados = 0
    errores = []

    for poliza_dict, reglas in zip(polizas_dicts, resultados):
        try:
            db.execute(text("""
                UPDATE polizas SET
                    largo_poliza = :largo, raiz_poliza_6 = :raiz6,
                    terminacion = :term, num_reexpediciones = :nreexp,
                    id_compuesto = :id_comp,
                    es_reexpedicion = :reexp, primer_anio = :primer,
                    fecha_aplicacion = :fec_apli, mes_aplicacion = :mes_apli,
                    pendientes_pago = :pend, trimestre = :trim,
                    flag_pagada = :fpag, flag_nueva_formal = :fnueva,
                    prima_anual_pesos = :pap, equivalencias_emitidas = :eqe,
                    equivalencias_pagadas = :eqp, flag_cancelada = :fcanc,
                    prima_proporcional = :pprop, condicional_prima = :cprim,
                    prima_acumulada_basica = :pacum,
                    updated_at = datetime('now')
                WHERE id = :id
            """), {
                "id": poliza_dict["id"],
                "largo": reglas["largo_poliza"], "raiz6": reglas["raiz_poliza_6"],
                "term": reglas["terminacion"], "nreexp": reglas["num_reexpediciones"],
                "id_comp": reglas["id_compuesto"],
                "reexp": reglas["es_reexpedicion"], "primer": reglas["primer_anio"],
                "fec_apli": reglas["fecha_aplicacion"], "mes_apli": reglas["mes_aplicacion"],
                "pend": reglas["pendientes_pago"], "trim": reglas["trimestre"],
                "fpag": reglas["flag_pagada"], "fnueva": reglas["flag_nueva_formal"],
                "pap": reglas["prima_anual_pesos"], "eqe": reglas["equivalencias_emitidas"],
                "eqp": reglas["equivalencias_pagadas"], "fcanc": reglas["flag_cancelada"],
                "pprop": reglas["prima_proporcional"], "cprim": reglas["condicional_prima"],
                "pacum": reglas["prima_acumulada_basica"],
            })
            actualizados += 1
        except Exception as e:
            errores.append(f"Póliza {poliza_dict.get('poliza_original')}: {str(e)}")

    db.commit()

    return ImportacionResult(
        success=True,
        registros_procesados=len(polizas_dicts),
        registros_nuevos=0,
        registros_actualizados=actualizados,
        registros_error=len(errores),
        errores=errores[:10],
        mensaje=f"Reglas aplicadas: {actualizados} pólizas actualizadas de {len(polizas_dicts)} procesadas"
    )


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


# ═══════════════════════════════════════════════════════════════════
# FINANZAS — Ingresos vs Egresos y Proyecciones (Fase 4)
# ═══════════════════════════════════════════════════════════════════
router_finanzas = APIRouter(prefix="/finanzas", tags=["Finanzas"])


@router_finanzas.get("", response_model=FinanzasResponse)
def get_finanzas(
    anio: int = Query(2025, description="Año de análisis"),
    ramo: Optional[str] = Query(None, description="Filtrar por ramo: vida, gmm"),
    db: Session = Depends(get_db)
):
    """
    Dashboard Financiero: Ingresos vs Egresos, Proyección de Cierre,
    Presupuesto IDEAL, y Tendencias Interanuales (Fase 4).
    """
    from datetime import datetime
    import math

    hoy = datetime.now()
    mes_actual = hoy.month

    # ── Base query ──
    q = db.query(Poliza).join(Producto, Poliza.producto_id == Producto.id, isouter=True)
    q_ant = db.query(Poliza).join(Producto, Poliza.producto_id == Producto.id, isouter=True)

    if ramo:
        ramo_u = ramo.upper()
        if "VIDA" in ramo_u:
            q = q.filter(Producto.ramo_codigo == 11)
            q_ant = q_ant.filter(Producto.ramo_codigo == 11)
        elif "GMM" in ramo_u:
            q = q.filter(Producto.ramo_codigo == 34)
            q_ant = q_ant.filter(Producto.ramo_codigo == 34)

    polizas_act = q.filter(Poliza.anio_aplicacion == anio).all()
    polizas_ant = q_ant.filter(Poliza.anio_aplicacion == anio - 1).all()

    # ── Ingresos vs Egresos por mes (4.1) ──
    meses_data = {}
    for m in range(1, 13):
        meses_data[m] = {
            "prima_cobrada": 0, "comision": 0,
            "prima_nueva": 0, "prima_sub": 0, "cancelaciones": 0,
        }

    for p in polizas_act:
        per = p.periodo_aplicacion or ""
        try:
            m = int(per.split("-")[1]) if "-" in per else 0
        except (ValueError, IndexError):
            m = 0
        if m < 1 or m > 12:
            continue

        pn = p.prima_neta or 0
        ms = (p.mystatus or "").upper()
        is_cancelled = "CANCEL" in ms or "CANC" in ms

        if is_cancelled:
            meses_data[m]["cancelaciones"] += pn
        else:
            meses_data[m]["prima_cobrada"] += pn
            # Estimate commission at ~8% average
            com = pn * (p.pct_comision or 0.08)
            meses_data[m]["comision"] += com

            if p.tipo_poliza == "NUEVA":
                meses_data[m]["prima_nueva"] += pn
            else:
                meses_data[m]["prima_sub"] += pn

    ingresos_egresos = []
    for m in range(1, 13):
        d = meses_data[m]
        ingreso = d["prima_cobrada"]
        egreso = d["comision"]
        margen = ingreso - egreso
        pct = round((margen / ingreso * 100) if ingreso > 0 else 0, 1)
        ingresos_egresos.append(IngresoEgresoMensual(
            mes=MESES_COMPLETOS.get(m, str(m)),
            mes_num=m,
            prima_cobrada=round(ingreso, 2),
            comision_pagada=round(egreso, 2),
            margen=round(margen, 2),
            pct_margen=pct,
            prima_nueva=round(d["prima_nueva"], 2),
            prima_subsecuente=round(d["prima_sub"], 2),
            cancelaciones=round(d["cancelaciones"], 2),
        ))

    # ── Proyección de Cierre (4.2) ──
    meses_con_data = [ie for ie in ingresos_egresos if ie.prima_cobrada > 0]
    n_meses = len(meses_con_data)
    prima_acumulada = sum(ie.prima_cobrada for ie in ingresos_egresos)
    promedio = prima_acumulada / n_meses if n_meses > 0 else 0
    proyeccion_anual = promedio * 12 if n_meses > 0 else 0

    # Linear regression for trend
    tendencia_str = "estable"
    confianza = 0.0
    if n_meses >= 3:
        xs = [ie.mes_num for ie in meses_con_data]
        ys = [ie.prima_cobrada for ie in meses_con_data]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        ss_xx = sum((x - mean_x) ** 2 for x in xs)
        ss_yy = sum((y - mean_y) ** 2 for y in ys)

        if ss_xx > 0:
            slope = ss_xy / ss_xx
            intercept = mean_y - slope * mean_x
            # Project remaining months
            proj_total = sum(max(0, slope * m + intercept) for m in range(1, 13))
            proyeccion_anual = proj_total

            # R²
            if ss_yy > 0:
                r_sq = (ss_xy ** 2) / (ss_xx * ss_yy)
                confianza = round(min(r_sq, 1.0), 3)

            if slope > promedio * 0.02:
                tendencia_str = "arriba"
            elif slope < -promedio * 0.02:
                tendencia_str = "abajo"

    # Get meta from presupuestos
    meta_row = db.query(Presupuesto).filter(
        Presupuesto.anio == anio,
        Presupuesto.periodo.is_(None),
    )
    if ramo:
        ramo_u = ramo.upper()
        if "VIDA" in ramo_u:
            meta_row = meta_row.filter(Presupuesto.ramo == "VIDA")
        elif "GMM" in ramo_u:
            meta_row = meta_row.filter(Presupuesto.ramo == "GMM")
    meta_rows = meta_row.all()
    meta_anual = sum(m.meta_prima_total or 0 for m in meta_rows) if meta_rows else proyeccion_anual

    var_vs_meta = round((proyeccion_anual - meta_anual) / meta_anual * 100, 1) if meta_anual > 0 else 0

    proyeccion = ProyeccionCierre(
        prima_acumulada=round(prima_acumulada, 2),
        meses_transcurridos=n_meses,
        promedio_mensual=round(promedio, 2),
        proyeccion_anual=round(proyeccion_anual, 2),
        meta_anual=round(meta_anual, 2),
        variacion_vs_meta=var_vs_meta,
        tendencia=tendencia_str,
        confianza=confianza,
    )

    # ── Presupuesto IDEAL vs Real (4.3) ──
    presupuesto_comp = []
    acum_meta = 0
    acum_real = 0
    for m in range(1, 13):
        periodo_str = f"{anio}-{m:02d}"
        pres_rows = db.query(Presupuesto).filter(
            Presupuesto.anio == anio,
            Presupuesto.periodo == periodo_str,
        )
        if ramo:
            ramo_u = ramo.upper()
            if "VIDA" in ramo_u:
                pres_rows = pres_rows.filter(Presupuesto.ramo == "VIDA")
            elif "GMM" in ramo_u:
                pres_rows = pres_rows.filter(Presupuesto.ramo == "GMM")
        pres_list = pres_rows.all()
        meta_mes = sum(p.meta_prima_total or 0 for p in pres_list) if pres_list else meta_anual / 12
        real_mes = meses_data[m]["prima_cobrada"]

        acum_meta += meta_mes
        acum_real += real_mes
        var = round((real_mes - meta_mes) / meta_mes * 100, 1) if meta_mes > 0 else 0

        presupuesto_comp.append(PresupuestoMensualComp(
            mes=MESES_COMPLETOS.get(m, str(m)),
            meta=round(meta_mes, 2),
            real=round(real_mes, 2),
            variacion=var,
            acumulado_meta=round(acum_meta, 2),
            acumulado_real=round(acum_real, 2),
        ))

    # ── Tendencia Interanual (4.4) ──
    meses_ant_data = {}
    for p in polizas_ant:
        per = p.periodo_aplicacion or ""
        try:
            m = int(per.split("-")[1]) if "-" in per else 0
        except (ValueError, IndexError):
            m = 0
        if 1 <= m <= 12:
            ms = (p.mystatus or "").upper()
            if "CANCEL" not in ms and "CANC" not in ms:
                meses_ant_data[m] = meses_ant_data.get(m, 0) + (p.prima_neta or 0)

    tendencia = []
    acum_ant = 0
    acum_act = 0
    acum_m = 0
    for m in range(1, 13):
        ant_val = meses_ant_data.get(m, 0)
        act_val = meses_data[m]["prima_cobrada"]
        meta_m = meta_anual / 12
        acum_ant += ant_val
        acum_act += act_val
        acum_m += meta_m
        tendencia.append(TendenciaAnual(
            mes=MESES_NOMBRE.get(m, str(m)),
            anio_anterior=round(ant_val, 2),
            anio_actual=round(act_val, 2),
            meta=round(meta_m, 2),
            acum_anterior=round(acum_ant, 2),
            acum_actual=round(acum_act, 2),
            acum_meta=round(acum_m, 2),
        ))

    # ── Resumen KPIs (4.1) ──
    comision_total = sum(ie.comision_pagada for ie in ingresos_egresos)
    margen_total = prima_acumulada - comision_total
    prima_ant_total = sum(meses_ant_data.values())
    var_inter = round((prima_acumulada - prima_ant_total) / prima_ant_total * 100, 1) if prima_ant_total > 0 else 0
    pct_cumpl = round(prima_acumulada / meta_anual * 100, 1) if meta_anual > 0 else 0

    mejor = max(ingresos_egresos, key=lambda x: x.prima_cobrada) if ingresos_egresos else None
    peor = min([ie for ie in ingresos_egresos if ie.prima_cobrada > 0], key=lambda x: x.prima_cobrada, default=None)

    resumen = ResumenFinanciero(
        prima_cobrada_total=round(prima_acumulada, 2),
        comision_total=round(comision_total, 2),
        margen_total=round(margen_total, 2),
        pct_margen=round((margen_total / prima_acumulada * 100) if prima_acumulada > 0 else 0, 1),
        meta_anual=round(meta_anual, 2),
        pct_cumplimiento=pct_cumpl,
        proyeccion_cierre=round(proyeccion_anual, 2),
        variacion_interanual=var_inter,
        mejor_mes=mejor.mes if mejor else None,
        peor_mes=peor.mes if peor else None,
    )

    return FinanzasResponse(
        resumen=resumen,
        ingresos_egresos=ingresos_egresos,
        proyeccion=proyeccion,
        presupuesto=presupuesto_comp,
        tendencia=tendencia,
        filtros_disponibles={
            "ramos": ["vida", "gmm"],
            "anios": [2022, 2023, 2024, 2025, 2026],
        },
    )


# ═══════════════════════════════════════════════════════════════════
# CONTRATANTES (Fase 5.1)
# ═══════════════════════════════════════════════════════════════════
router_contratantes = APIRouter(prefix="/contratantes", tags=["Contratantes"])


@router_contratantes.get("", response_model=List[ContratanteOut])
def list_contratantes(
    q: Optional[str] = Query(None, description="Búsqueda por nombre/RFC"),
    agente_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Contratante)
    if q:
        query = query.filter(
            (Contratante.nombre.ilike(f"%{q}%")) |
            (Contratante.rfc.ilike(f"%{q}%"))
        )
    if agente_id:
        query = query.filter(Contratante.agente_id == agente_id)
    contratantes = query.order_by(Contratante.nombre).all()

    result = []
    for c in contratantes:
        pols = db.query(Poliza).filter(Poliza.contratante_id == c.id).all()
        ref_nombre = None
        if c.referido_por_id:
            ref = db.query(Contratante).get(c.referido_por_id)
            ref_nombre = ref.nombre if ref else None
        result.append(ContratanteOut(
            id=c.id, nombre=c.nombre, rfc=c.rfc, telefono=c.telefono,
            email=c.email, domicilio=c.domicilio, notas=c.notas,
            referido_por_id=c.referido_por_id, agente_id=c.agente_id,
            num_polizas=len(pols),
            prima_total=sum(p.prima_neta or 0 for p in pols),
            referido_por_nombre=ref_nombre,
            created_at=c.created_at,
        ))
    return result


@router_contratantes.post("", response_model=ContratanteOut, status_code=201)
def create_contratante(data: ContratanteCreate, db: Session = Depends(get_db)):
    c = Contratante(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return ContratanteOut(
        id=c.id, nombre=c.nombre, rfc=c.rfc, telefono=c.telefono,
        email=c.email, domicilio=c.domicilio, notas=c.notas,
        referido_por_id=c.referido_por_id, agente_id=c.agente_id,
        created_at=c.created_at,
    )


@router_contratantes.put("/{contratante_id}", response_model=ContratanteOut)
def update_contratante(contratante_id: int, data: ContratanteCreate, db: Session = Depends(get_db)):
    c = db.query(Contratante).get(contratante_id)
    if not c:
        raise HTTPException(404, "Contratante no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    from datetime import datetime
    c.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(c)
    pols = db.query(Poliza).filter(Poliza.contratante_id == c.id).all()
    return ContratanteOut(
        id=c.id, nombre=c.nombre, rfc=c.rfc, telefono=c.telefono,
        email=c.email, domicilio=c.domicilio, notas=c.notas,
        referido_por_id=c.referido_por_id, agente_id=c.agente_id,
        num_polizas=len(pols),
        prima_total=sum(p.prima_neta or 0 for p in pols),
        created_at=c.created_at,
    )


# ═══════════════════════════════════════════════════════════════════
# SOLICITUDES — Pipeline de emisión (Fase 5.2)
# ═══════════════════════════════════════════════════════════════════
router_solicitudes = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])


@router_solicitudes.get("", response_model=SolicitudesResponse)
def list_solicitudes(
    estado: Optional[str] = None,
    agente_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Solicitud)
    if estado:
        query = query.filter(Solicitud.estado == estado.upper())
    if agente_id:
        query = query.filter(Solicitud.agente_id == agente_id)
    sols = query.order_by(Solicitud.created_at.desc()).all()

    sol_list = []
    for s in sols:
        ag = db.query(Agente).get(s.agente_id) if s.agente_id else None
        ct = db.query(Contratante).get(s.contratante_id) if s.contratante_id else None
        sol_list.append(SolicitudOut(
            id=s.id, folio=s.folio, agente_id=s.agente_id,
            contratante_id=s.contratante_id, ramo=s.ramo, plan=s.plan,
            suma_asegurada=s.suma_asegurada, prima_estimada=s.prima_estimada,
            estado=s.estado, fecha_solicitud=s.fecha_solicitud,
            poliza_id=s.poliza_id, fecha_emision=s.fecha_emision,
            fecha_pago=s.fecha_pago, notas=s.notas,
            agente_nombre=ag.nombre_completo if ag else None,
            contratante_nombre=ct.nombre if ct else None,
            created_at=s.created_at, updated_at=s.updated_at,
        ))

    # Pipeline stats
    all_sols = db.query(Solicitud).all()
    pipeline = PipelineResumen(
        total=len(all_sols),
        tramite=sum(1 for s in all_sols if s.estado == "TRAMITE"),
        emitida=sum(1 for s in all_sols if s.estado == "EMITIDA"),
        pagada=sum(1 for s in all_sols if s.estado == "PAGADA"),
        rechazada=sum(1 for s in all_sols if s.estado == "RECHAZADA"),
        cancelada=sum(1 for s in all_sols if s.estado == "CANCELADA"),
        prima_estimada_total=sum(s.prima_estimada or 0 for s in all_sols),
        prima_pagada_total=sum(s.prima_estimada or 0 for s in all_sols if s.estado == "PAGADA"),
    )

    return SolicitudesResponse(solicitudes=sol_list, pipeline=pipeline)


@router_solicitudes.post("", response_model=SolicitudOut, status_code=201)
def create_solicitud(data: SolicitudCreate, db: Session = Depends(get_db)):
    from datetime import datetime
    # Auto-generate folio if not provided
    folio = data.folio
    if not folio:
        count = db.query(Solicitud).count()
        folio = f"SOL-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

    s = Solicitud(**data.model_dump(exclude={"folio"}), folio=folio)
    if not s.fecha_solicitud:
        s.fecha_solicitud = datetime.now().strftime("%Y-%m-%d")
    db.add(s)
    db.commit()
    db.refresh(s)
    return SolicitudOut(
        id=s.id, folio=s.folio, agente_id=s.agente_id,
        contratante_id=s.contratante_id, ramo=s.ramo, plan=s.plan,
        suma_asegurada=s.suma_asegurada, prima_estimada=s.prima_estimada,
        estado=s.estado, fecha_solicitud=s.fecha_solicitud,
        created_at=s.created_at,
    )


@router_solicitudes.put("/{solicitud_id}", response_model=SolicitudOut)
def update_solicitud(solicitud_id: int, data: SolicitudUpdate, db: Session = Depends(get_db)):
    s = db.query(Solicitud).get(solicitud_id)
    if not s:
        raise HTTPException(404, "Solicitud no encontrada")
    from datetime import datetime
    for k, v in data.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(s, k, v)
    s.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(s)
    ag = db.query(Agente).get(s.agente_id) if s.agente_id else None
    ct = db.query(Contratante).get(s.contratante_id) if s.contratante_id else None
    return SolicitudOut(
        id=s.id, folio=s.folio, agente_id=s.agente_id,
        contratante_id=s.contratante_id, ramo=s.ramo, plan=s.plan,
        suma_asegurada=s.suma_asegurada, prima_estimada=s.prima_estimada,
        estado=s.estado, fecha_solicitud=s.fecha_solicitud,
        poliza_id=s.poliza_id, fecha_emision=s.fecha_emision,
        fecha_pago=s.fecha_pago, notas=s.notas,
        agente_nombre=ag.nombre_completo if ag else None,
        contratante_nombre=ct.nombre if ct else None,
        created_at=s.created_at, updated_at=s.updated_at,
    )


# ═══════════════════════════════════════════════════════════════════
# DISTRIBUCIÓN DE COMISIONES (Fase 5.3)
# ═══════════════════════════════════════════════════════════════════
router_comisiones = APIRouter(prefix="/comisiones", tags=["Comisiones"])


@router_comisiones.get("/distribuciones", response_model=List[DistribucionOut])
def list_distribuciones(
    agente_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(DistribucionComision).filter(DistribucionComision.activo == 1)
    if agente_id:
        query = query.filter(DistribucionComision.agente_id == agente_id)
    dists = query.all()

    result = []
    for d in dists:
        ag = db.query(Agente).get(d.agente_id) if d.agente_id else None
        sa = db.query(Agente).get(d.sub_agente_id) if d.sub_agente_id else None
        result.append(DistribucionOut(
            id=d.id, agente_id=d.agente_id, sub_agente_id=d.sub_agente_id,
            nombre_beneficiario=d.nombre_beneficiario, porcentaje=d.porcentaje,
            ramo=d.ramo, tipo=d.tipo, activo=d.activo,
            agente_nombre=ag.nombre_completo if ag else None,
            sub_agente_nombre=sa.nombre_completo if sa else None,
        ))
    return result


@router_comisiones.post("/distribuciones", response_model=DistribucionOut, status_code=201)
def create_distribucion(data: DistribucionCreate, db: Session = Depends(get_db)):
    # Validate sum per agent ≤ 100%
    existing = db.query(DistribucionComision).filter(
        DistribucionComision.agente_id == data.agente_id,
        DistribucionComision.activo == 1,
    ).all()
    total_pct = sum(d.porcentaje for d in existing) + data.porcentaje
    if total_pct > 100:
        raise HTTPException(400, f"La distribución total excede 100% ({total_pct}%)")

    d = DistribucionComision(**data.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    ag = db.query(Agente).get(d.agente_id) if d.agente_id else None
    return DistribucionOut(
        id=d.id, agente_id=d.agente_id, sub_agente_id=d.sub_agente_id,
        nombre_beneficiario=d.nombre_beneficiario, porcentaje=d.porcentaje,
        ramo=d.ramo, tipo=d.tipo, activo=d.activo,
        agente_nombre=ag.nombre_completo if ag else None,
    )


# ═══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DINÁMICA (Fase 5.5)
# ═══════════════════════════════════════════════════════════════════
router_configuracion = APIRouter(prefix="/configuracion", tags=["Configuración"])


CONFIGURACIONES_DEFAULT = [
    {"clave": "umbral_comision_vida", "valor": "0.021", "tipo": "numero", "grupo": "umbrales", "descripcion": "Umbral de comisión para clasificar prima Vida como BÁSICA (2.1%)"},
    {"clave": "umbral_comision_excedente", "valor": "0.021", "tipo": "numero", "grupo": "umbrales", "descripcion": "Umbral debajo del cual la prima Vida es EXCEDENTE"},
    {"clave": "tc_udis", "valor": "8.23", "tipo": "numero", "grupo": "tipos_cambio", "descripcion": "Tipo de cambio UDIs a MXN"},
    {"clave": "tc_usd", "valor": "17.50", "tipo": "numero", "grupo": "tipos_cambio", "descripcion": "Tipo de cambio USD a MXN"},
    {"clave": "dias_gracia_pago", "valor": "30", "tipo": "numero", "grupo": "umbrales", "descripcion": "Días de gracia para considerar un pago como pendiente"},
    {"clave": "meta_trimestral_pct", "valor": "25", "tipo": "numero", "grupo": "umbrales", "descripcion": "Porcentaje esperado de cumplimiento trimestral"},
    {"clave": "anio_fiscal", "valor": "2025", "tipo": "numero", "grupo": "general", "descripcion": "Año fiscal del ejercicio actual"},
    {"clave": "catalogo_segmentos", "valor": "[\"ALFA TOP INTEGRAL\",\"ALFA TOP COMBINADO\",\"ALFA TOP\",\"ALFA INTEGRAL\",\"ALFA/BETA\",\"BETA1\",\"BETA2\",\"OMEGA\"]", "tipo": "json", "grupo": "catalogos", "descripcion": "Catálogo de segmentos comerciales"},
    {"clave": "catalogo_estatus", "valor": "[\"PAGADA\",\"AL CORRIENTE\",\"ATRASADA\",\"CANCELADA\",\"PENDIENTE DE PAGO\",\"REHABILITADA\"]", "tipo": "json", "grupo": "catalogos", "descripcion": "Catálogo de estatus internos del sistema"},
]


@router_configuracion.get("", response_model=ConfiguracionResponse)
def get_configuracion(
    grupo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Seed defaults if empty
    if db.query(Configuracion).count() == 0:
        for c in CONFIGURACIONES_DEFAULT:
            db.add(Configuracion(**c))
        db.commit()

    query = db.query(Configuracion)
    if grupo:
        query = query.filter(Configuracion.grupo == grupo)
    configs = query.order_by(Configuracion.grupo, Configuracion.clave).all()

    grupos = sorted(set(c.grupo for c in db.query(Configuracion).all() if c.grupo))

    return ConfiguracionResponse(
        configuraciones=[
            ConfiguracionItem(
                clave=c.clave, valor=c.valor, tipo=c.tipo,
                grupo=c.grupo, descripcion=c.descripcion
            ) for c in configs
        ],
        grupos=grupos,
    )


@router_configuracion.put("/{clave}", response_model=ConfiguracionItem)
def update_configuracion(clave: str, data: ConfiguracionUpdate, db: Session = Depends(get_db)):
    c = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if not c:
        raise HTTPException(404, f"Configuración '{clave}' no encontrada")
    from datetime import datetime
    c.valor = data.valor
    c.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(c)
    return ConfiguracionItem(
        clave=c.clave, valor=c.valor, tipo=c.tipo,
        grupo=c.grupo, descripcion=c.descripcion,
    )
