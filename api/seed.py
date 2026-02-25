"""
Seed de datos de demostración para MAG Sistema.
Se ejecuta al iniciar la app si la base de datos está vacía.
"""
from sqlalchemy.orm import Session
from .database import (
    SessionLocal, Agente, Producto, Poliza, IndicadorAxa, Meta,
    Segmento, Recibo, GestionComercial, Presupuesto,
    Contratante, Solicitud, Configuracion,
)
from datetime import datetime

AGENTES_DEMO = [
    {"codigo_agente": "47968",  "nombre_completo": "GARCÍA LÓPEZ, ROBERTO",   "rol": "Agente",        "situacion": "ACTIVO",    "fecha_alta": "2018-03-15", "territorio": "Zona Norte",   "oficina": "CDMX Norte",   "gerencia": "Gerencia A", "centro_costos": "56991"},
    {"codigo_agente": "627523", "nombre_completo": "MARTÍNEZ SOTO, PATRICIA", "rol": "Agente",        "situacion": "ACTIVO",    "fecha_alta": "2019-07-22", "territorio": "Zona Sur",     "oficina": "CDMX Sur",     "gerencia": "Gerencia B", "centro_costos": "606266"},
    {"codigo_agente": "385201", "nombre_completo": "HERNÁNDEZ RUIZ, CARLOS",  "rol": "Agente Senior", "situacion": "ACTIVO",    "fecha_alta": "2017-01-10", "territorio": "Zona Centro",  "oficina": "CDMX Centro",  "gerencia": "Gerencia A", "centro_costos": "57834"},
    {"codigo_agente": "492011", "nombre_completo": "TORRES VEGA, ANA LAURA",  "rol": "Agente",        "situacion": "ACTIVO",    "fecha_alta": "2020-11-05", "territorio": "Zona Oriente", "oficina": "CDMX Oriente", "gerencia": "Gerencia C", "centro_costos": "61204"},
    {"codigo_agente": "731804", "nombre_completo": "RAMÍREZ CASTILLO, MIGUEL","rol": "Agente",        "situacion": "ACTIVO",    "fecha_alta": "2021-04-18", "territorio": "Zona Norte",   "oficina": "CDMX Norte",   "gerencia": "Gerencia A", "centro_costos": "58902"},
    {"codigo_agente": "203847", "nombre_completo": "FLORES MENDOZA, DIANA",   "rol": "Agente",        "situacion": "CANCELADO", "fecha_alta": "2016-09-30", "fecha_cancelacion": "2024-06-01", "territorio": "Zona Sur", "oficina": "CDMX Sur", "gerencia": "Gerencia B", "centro_costos": "55410"},
    {"codigo_agente": "918273", "nombre_completo": "JIMÉNEZ REYES, OSCAR",    "rol": "Agente Senior", "situacion": "ACTIVO",    "fecha_alta": "2015-02-14", "territorio": "Zona Centro",  "oficina": "CDMX Centro",  "gerencia": "Gerencia B", "centro_costos": "59301"},
    {"codigo_agente": "564738", "nombre_completo": "MORALES PAREDES, LUCÍA",  "rol": "Agente",        "situacion": "ACTIVO",    "fecha_alta": "2022-08-20", "territorio": "Zona Oriente", "oficina": "CDMX Oriente", "gerencia": "Gerencia C", "centro_costos": "62105"},
]

PRODUCTOS_DEMO = [
    {"ramo_codigo": 11, "ramo_nombre": "VIDA",                              "plan": "VIDA Y AHORRO",   "gama": None},
    {"ramo_codigo": 11, "ramo_nombre": "VIDA",                              "plan": "MI PROYECTO R",   "gama": None},
    {"ramo_codigo": 11, "ramo_nombre": "VIDA",                              "plan": "SOLUCIÓN MAYOR",  "gama": None},
    {"ramo_codigo": 34, "ramo_nombre": "GASTOS MEDICOS MAYORES INDIVIDUAL", "plan": "FLEX PLUS",       "gama": "ZAFIRO"},
    {"ramo_codigo": 34, "ramo_nombre": "GASTOS MEDICOS MAYORES INDIVIDUAL", "plan": "FLEX PLUS",       "gama": "ESMERALDA"},
    {"ramo_codigo": 34, "ramo_nombre": "GASTOS MEDICOS MAYORES INDIVIDUAL", "plan": "FLEX PLUS",       "gama": "DIAMANTE"},
    {"ramo_codigo": 34, "ramo_nombre": "GASTOS MEDICOS MAYORES INDIVIDUAL", "plan": "FLEX PLUS",       "gama": "RUBI"},
]

METAS_DEMO = [
    {"anio": 2025, "periodo": None, "meta_polizas_vida": 48, "meta_equiv_vida": 64.0, "meta_prima_vida": 1_440_000, "meta_polizas_gmm": 240, "meta_asegurados_gmm": 600, "meta_prima_gmm": 5_760_000},
    {"anio": 2025, "periodo": "2025-01", "meta_polizas_vida": 4, "meta_equiv_vida": 5.3, "meta_prima_vida": 120_000, "meta_polizas_gmm": 20, "meta_asegurados_gmm": 50, "meta_prima_gmm": 480_000},
]

# Catálogo completo de segmentos (Fase 3.2)
SEGMENTOS_DEMO = [
    {"nombre": "ALFA TOP INTEGRAL",  "agrupado": "ALFA",  "orden": 1},
    {"nombre": "ALFA TOP COMBINADO", "agrupado": "ALFA",  "orden": 2},
    {"nombre": "ALFA TOP",           "agrupado": "ALFA",  "orden": 3},
    {"nombre": "ALFA INTEGRAL",      "agrupado": "ALFA",  "orden": 4},
    {"nombre": "ALFA/BETA",          "agrupado": "ALFA",  "orden": 5},
    {"nombre": "BETA1",              "agrupado": "BETA",  "orden": 6},
    {"nombre": "BETA2",              "agrupado": "BETA",  "orden": 7},
    {"nombre": "OMEGA",              "agrupado": "OMEGA", "orden": 8},
]

# Gestiones comerciales (Fase 3.5)
GESTIONES_DEMO = [
    {"nombre": "ALFA/MARIA ESTHER",   "lider_codigo": "63931", "lider_nombre": "MARÍA ESTHER LUNA",   "tipo": "ALFA"},
    {"nombre": "MARIO FLORES",        "lider_codigo": "63931", "lider_nombre": "MARIO FLORES",         "tipo": "BETA"},
    {"nombre": "DIRECTA/PROMOTORA",   "lider_codigo": "63931", "lider_nombre": "MAG PROMOTORIA",       "tipo": "DIRECTA"},
]

# Asignación de segmentos y gestiones a agentes demo
AGENTE_SEGMENTOS = {
    "47968":  {"segmento_nombre": "ALFA TOP INTEGRAL",  "segmento_agrupado": "ALFA",  "gestion_comercial": "ALFA/MARIA ESTHER"},
    "627523": {"segmento_nombre": "BETA1",              "segmento_agrupado": "BETA",  "gestion_comercial": "MARIO FLORES"},
    "385201": {"segmento_nombre": "OMEGA",              "segmento_agrupado": "OMEGA", "gestion_comercial": "DIRECTA/PROMOTORA"},
    "492011": {"segmento_nombre": "ALFA INTEGRAL",      "segmento_agrupado": "ALFA",  "gestion_comercial": "ALFA/MARIA ESTHER"},
    "731804": {"segmento_nombre": "BETA2",              "segmento_agrupado": "BETA",  "gestion_comercial": "MARIO FLORES"},
    "203847": {"segmento_nombre": "OMEGA",              "segmento_agrupado": "OMEGA", "gestion_comercial": "DIRECTA/PROMOTORA"},
    "918273": {"segmento_nombre": "ALFA TOP COMBINADO", "segmento_agrupado": "ALFA",  "gestion_comercial": "ALFA/MARIA ESTHER"},
    "564738": {"segmento_nombre": "BETA1",              "segmento_agrupado": "BETA",  "gestion_comercial": "MARIO FLORES"},
}



def _fake_polizas(agente_ids: list[int], prod_ids_vida: list[int], prod_ids_gmm_map: dict) -> list[dict]:
    """Genera 110 pólizas de ejemplo realistas."""
    import random
    random.seed(42)

    gamas = ["ZAFIRO", "ESMERALDA", "DIAMANTE", "RUBI"]
    formas_pago = ["ANUAL", "SEMESTRAL", "TRIMESTRAL", "MENSUAL"]
    tipos_pago = ["Agente", "Tarjeta", "CARGO AUTOMATICO", "Domiciliación"]
    nombres = [
        "RIVERA SANTOS, LUCIA", "GÓMEZ PÉREZ, CARLOS", "MORENO SILVA, DIANA",
        "CASTILLO RUIZ, JORGE", "VEGA MORALES, CARMEN", "REYES FLORES, MIGUEL",
        "HERNÁNDEZ LUNA, SOFÍA", "MENDOZA PAREDES, ANDRÉS", "ORTIZ SOTO, VALERIA",
        "ROMERO GARZA, PABLO", "VARGAS TORRES, CRISTINA", "SALINAS ORTEGA, ROBERTO",
        "MIRANDA BONILLA, VERÓNICA", "CARRILLO TEJEDA, HUGO", "ESPINOSA VALDEZ, MARIO",
        "MOLINA CANTU, ISRAEL", "CERVANTES GALINDO, ANA KAREN", "ACOSTA LIMA, PEDRO",
        "FUENTES IBARRA, ELENA", "CABRERA NAVA, FRANCISCO",
    ]

    polizas = []
    pid = 0
    for anio in [2025, 2024]:
        for mes in range(1, 13):
            for agente_id in agente_ids[:5]:
                # GMM
                gama = gamas[(pid) % 4]
                prod_gmm = prod_ids_gmm_map.get(gama)
                prima_neta = random.choice([21000, 24500, 27000, 32000, 35000])
                iva = round(prima_neta * 0.16, 2)
                recargo = round(prima_neta * 0.09, 2)
                num_as = random.randint(1, 5)
                fp = random.choice(formas_pago)
                fecha_ini = f"{anio}-{mes:02d}-{random.randint(1,28):02d}"
                fecha_fin = f"{anio+1}-{mes:02d}-{random.randint(1,28):02d}"
                status = "PAGADA" if random.random() > 0.07 else "CANC/X F.PAGO"
                tipo = "NUEVA" if anio >= 2025 else "SUBSECUENTE"
                polizas.append({
                    "poliza_original": f"1{pid:04d}U00",
                    "poliza_estandar": f"1{pid:04d}U00",
                    "agente_id": agente_id,
                    "producto_id": prod_gmm,
                    "asegurado_nombre": nombres[pid % len(nombres)],
                    "num_asegurados": num_as,
                    "fecha_inicio": fecha_ini,
                    "fecha_fin": fecha_fin,
                    "prima_total": round(prima_neta + iva + recargo, 2),
                    "prima_neta": prima_neta,
                    "iva": iva, "recargo": recargo,
                    "suma_asegurada": random.choice([10_000_000, 20_000_000, 30_000_000, 40_000_000]),
                    "deducible": random.choice([50000, 60000, 70000, 80000]),
                    "coaseguro": 10.0,
                    "forma_pago": fp,
                    "tipo_pago": random.choice(tipos_pago),
                    "status_recibo": status,
                    "gama": gama,
                    "tipo_poliza": tipo if status == "PAGADA" else "NUEVA",
                    "tipo_prima": None,
                    "es_nueva": tipo == "NUEVA" and status == "PAGADA",
                    "mystatus": "PAGADA" if status == "PAGADA" else "CANCELADA CADUCADA",
                    "periodo_aplicacion": f"{anio}-{mes:02d}",
                    "anio_aplicacion": anio,
                    "fuente": "EXCEL_IMPORT",
                })
                pid += 1

    # Vida
    for anio in [2025, 2024]:
        meses_vida = [1, 4, 7, 10] if anio == 2025 else [2, 5, 8, 11]
        prods = prod_ids_vida
        for i, mes in enumerate(meses_vida):
            agente_id = agente_ids[i % len(agente_ids[:4])]
            prod = prods[i % len(prods)]
            prima_neta = random.choice([36600, 42000, 47400, 52800])
            comision = round(prima_neta * 0.025, 2)  # Básica > 2.1%
            fecha_ini = f"{anio}-{mes:02d}-15"
            fecha_fin = f"{anio+30}-{mes:02d}-15"
            tipo = "NUEVA" if anio == 2025 else "SUBSECUENTE"
            polizas.append({
                "poliza_original": f"00764{pid:02d}A",
                "poliza_estandar": f"764{pid:02d}A",
                "agente_id": agente_id,
                "producto_id": prod,
                "asegurado_nombre": nombres[(pid * 3) % len(nombres)],
                "num_asegurados": 1,
                "fecha_inicio": fecha_ini,
                "fecha_fin": fecha_fin,
                "prima_total": prima_neta,
                "prima_neta": prima_neta,
                "iva": 0.0, "recargo": 0.0,
                "suma_asegurada": prima_neta * 50,
                "deducible": None, "coaseguro": None,
                "forma_pago": random.choice(formas_pago),
                "tipo_pago": random.choice(tipos_pago),
                "status_recibo": "PAGADA",
                "gama": None,
                "tipo_poliza": tipo,
                "tipo_prima": "BASICA",
                "pct_comision": 0.025,
                "es_nueva": tipo == "NUEVA",
                "mystatus": "PAGADA",
                "periodo_aplicacion": f"{anio}-{mes:02d}",
                "anio_aplicacion": anio,
                "fuente": "EXCEL_IMPORT",
            })
            pid += 1

    return polizas


def seed_demo(db: Session) -> bool:
    """Siembra datos si la base está vacía. Retorna True si seó, False si ya tenía datos."""
    if db.query(Agente).count() > 0:
        return False

    print("[SEED] Inicializando datos de demostración...")

    # ── Segmentos (Fase 3.2) ──
    segmentos_map = {}
    for s in SEGMENTOS_DEMO:
        seg = Segmento(**s)
        db.add(seg)
        segmentos_map[s["nombre"]] = seg
    db.flush()

    # ── Gestiones Comerciales (Fase 3.5) ──
    gestiones_map = {}
    for g in GESTIONES_DEMO:
        gc = GestionComercial(**g)
        db.add(gc)
        gestiones_map[g["nombre"]] = gc
    db.flush()

    # Agentes (con segmentos y gestiones asignados)
    agentes = []
    for a in AGENTES_DEMO:
        extra = AGENTE_SEGMENTOS.get(a["codigo_agente"], {})
        seg_nombre = extra.get("segmento_nombre")
        gestion_nombre = extra.get("gestion_comercial")

        ag = Agente(
            **{k: v for k, v in a.items() if v is not None},
            promotor="MAG Principal", nombre_promotoria="MAG",
            segmento_nombre=seg_nombre,
            segmento_agrupado=extra.get("segmento_agrupado"),
            gestion_comercial=gestion_nombre,
            lider_codigo="63931",
            estado="ACTIVO" if a.get("situacion") == "ACTIVO" else "CANCELADO",
            segmento_id=segmentos_map[seg_nombre].id if seg_nombre and seg_nombre in segmentos_map else None,
            gestion_id=gestiones_map[gestion_nombre].id if gestion_nombre and gestion_nombre in gestiones_map else None,
        )
        db.add(ag)
        agentes.append(ag)
    db.flush()

    # Productos
    productos = []
    for p in PRODUCTOS_DEMO:
        pr = Producto(**p)
        db.add(pr)
        productos.append(pr)
    db.flush()

    prod_vida = [p.id for p in productos if p.ramo_codigo == 11]
    prod_gmm_map = {p.gama: p.id for p in productos if p.ramo_codigo == 34 and p.gama}
    agente_ids = [a.id for a in agentes if a.situacion == "ACTIVO"]

    # Metas (with equiv field)
    for m in METAS_DEMO:
        db.add(Meta(**m))

    # Pólizas
    polizas_data = _fake_polizas(agente_ids, prod_vida, prod_gmm_map)
    for pd_data in polizas_data:
        db.add(Poliza(**pd_data))

    # Indicadores AXA ejemplo
    for codigo, pol, ramo, prima in [
        ("47968", "0076384A", "VIDA", 28077.0),
        ("627523", "10007U00", "GMM",  24568.0),
        ("385201", "10015Z00", "GMM",  18500.0),
        ("47968", "0088921B", "VIDA",  22400.0),
    ]:
        db.add(IndicadorAxa(
            periodo="2025-07",
            poliza=pol,
            agente_codigo=codigo,
            ramo=ramo,
            prima_primer_anio=prima,
            es_nueva_axa=True,
            reconocimiento_antiguedad=False,
            num_asegurados=1,
        ))

    # ── Presupuestos de ejemplo (Fase 3.4) ──
    for ramo_p, meta_total in [("VIDA", 1_440_000), ("GMM", 5_760_000)]:
        db.add(Presupuesto(
            anio=2025, periodo=None, ramo=ramo_p,
            meta_prima_total=meta_total,
            meta_polizas=48 if ramo_p == "VIDA" else 240,
            meta_equivalentes=64.0 if ramo_p == "VIDA" else 0,
            meta_asegurados=0 if ramo_p == "VIDA" else 600,
        ))
        for m in range(1, 13):
            db.add(Presupuesto(
                anio=2025, periodo=f"2025-{m:02d}", ramo=ramo_p,
                meta_prima_total=round(meta_total / 12, 2),
                meta_polizas=4 if ramo_p == "VIDA" else 20,
                meta_equivalentes=round(64.0 / 12, 2) if ramo_p == "VIDA" else 0,
                meta_asegurados=0 if ramo_p == "VIDA" else 50,
            ))

    # Actualizar conteo de agentes por gestión
    for gc_name, gc in gestiones_map.items():
        gc.num_agentes = sum(1 for a in agentes if a.gestion_comercial == gc_name)

    db.commit()

    # ── Contratantes demo (Fase 5.1) ──
    contratantes_demo = [
        {"nombre": "MARTINEZ LOPEZ, CARLOS", "rfc": "MALC780515AAA", "telefono": "5551234567", "email": "carlos.martinez@mail.com", "domicilio": "Av. Reforma 123, CDMX"},
        {"nombre": "GONZALEZ RUIZ, ANA MARIA", "rfc": "GORA850220BBB", "telefono": "5559876543", "email": "ana.gonzalez@mail.com", "domicilio": "Calle Juárez 456, Guadalajara"},
        {"nombre": "HERNANDEZ DIAZ, PEDRO", "rfc": "HEDP900101CCC", "telefono": "5554567890", "email": "pedro.hdz@mail.com"},
        {"nombre": "SANCHEZ VEGA, LAURA", "rfc": "SAVL880315DDD", "telefono": "5552345678"},
        {"nombre": "RAMIREZ SOTO, JORGE", "rfc": "RASJ920710EEE", "telefono": "5558765432", "email": "jorge.ramirez@mail.com", "domicilio": "Blvd. Avila Camacho 789, Naucalpan"},
        {"nombre": "FLORES MENDEZ, PATRICIA", "rfc": "FOMP750825FFF", "telefono": "5556789012"},
    ]
    contratantes = []
    for cd in contratantes_demo:
        c = Contratante(**cd)
        if len(contratantes) > 0:
            c.agente_id = agentes[len(contratantes) % len(agentes)].id
        db.add(c)
        contratantes.append(c)
    db.flush()
    # Referral chain: 3→1, 4→2, 6→5
    contratantes[2].referido_por_id = contratantes[0].id
    contratantes[3].referido_por_id = contratantes[1].id
    contratantes[5].referido_por_id = contratantes[4].id
    db.flush()

    # ── Solicitudes demo (Fase 5.2) ──
    solicitudes_demo = [
        {"folio": "SOL-202501-0001", "agente_id": agentes[0].id, "contratante_id": contratantes[0].id, "ramo": "VIDA", "plan": "Vida y Ahorro", "prima_estimada": 35000, "estado": "PAGADA", "fecha_solicitud": "2025-01-15", "fecha_emision": "2025-01-22", "fecha_pago": "2025-02-01"},
        {"folio": "SOL-202501-0002", "agente_id": agentes[1].id, "contratante_id": contratantes[1].id, "ramo": "GMM", "plan": "Flex Plus", "prima_estimada": 18500, "estado": "PAGADA", "fecha_solicitud": "2025-01-20", "fecha_emision": "2025-01-28", "fecha_pago": "2025-02-10"},
        {"folio": "SOL-202502-0001", "agente_id": agentes[2].id, "contratante_id": contratantes[2].id, "ramo": "VIDA", "plan": "Dotal Mixto", "prima_estimada": 42000, "estado": "EMITIDA", "fecha_solicitud": "2025-02-05", "fecha_emision": "2025-02-12"},
        {"folio": "SOL-202502-0002", "agente_id": agentes[0].id, "contratante_id": contratantes[3].id, "ramo": "GMM", "plan": "Óptima", "prima_estimada": 22000, "estado": "EMITIDA", "fecha_solicitud": "2025-02-10", "fecha_emision": "2025-02-18"},
        {"folio": "SOL-202502-0003", "agente_id": agentes[3].id, "contratante_id": contratantes[4].id, "ramo": "VIDA", "plan": "Vida y Ahorro Plus", "prima_estimada": 28000, "estado": "TRAMITE", "fecha_solicitud": "2025-02-15"},
        {"folio": "SOL-202502-0004", "agente_id": agentes[1].id, "contratante_id": contratantes[5].id, "ramo": "GMM", "plan": "Flex Plus Familiar", "prima_estimada": 45000, "estado": "TRAMITE", "fecha_solicitud": "2025-02-18"},
        {"folio": "SOL-202502-0005", "agente_id": agentes[4].id, "contratante_id": contratantes[0].id, "ramo": "VIDA", "plan": "Temporal 20", "prima_estimada": 15000, "estado": "RECHAZADA", "fecha_solicitud": "2025-02-01", "notas": "Rechazada por historial médico"},
        {"folio": "SOL-202502-0006", "agente_id": agentes[2].id, "contratante_id": contratantes[1].id, "ramo": "GMM", "plan": "Estándar", "prima_estimada": 12000, "estado": "CANCELADA", "fecha_solicitud": "2025-02-08", "notas": "Cliente desistió"},
    ]
    for sd in solicitudes_demo:
        db.add(Solicitud(**sd))

    # ── Configuraciones default (Fase 5.5) ──
    configs_default = [
        {"clave": "umbral_comision_vida", "valor": "0.021", "tipo": "numero", "grupo": "umbrales", "descripcion": "Umbral de comisión Vida BÁSICA (2.1%)"},
        {"clave": "umbral_comision_excedente", "valor": "0.021", "tipo": "numero", "grupo": "umbrales", "descripcion": "Umbral debajo del cual prima Vida es EXCEDENTE"},
        {"clave": "tc_udis", "valor": "8.23", "tipo": "numero", "grupo": "tipos_cambio", "descripcion": "Tipo de cambio UDIs a MXN"},
        {"clave": "tc_usd", "valor": "17.50", "tipo": "numero", "grupo": "tipos_cambio", "descripcion": "Tipo de cambio USD a MXN"},
        {"clave": "dias_gracia_pago", "valor": "30", "tipo": "numero", "grupo": "umbrales", "descripcion": "Días de gracia para pago pendiente"},
        {"clave": "meta_trimestral_pct", "valor": "25", "tipo": "numero", "grupo": "umbrales", "descripcion": "% esperado de cumplimiento trimestral"},
        {"clave": "anio_fiscal", "valor": "2025", "tipo": "numero", "grupo": "general", "descripcion": "Año fiscal del ejercicio actual"},
        {"clave": "catalogo_segmentos", "valor": '["ALFA TOP INTEGRAL","ALFA TOP COMBINADO","ALFA TOP","ALFA INTEGRAL","ALFA/BETA","BETA1","BETA2","OMEGA"]', "tipo": "json", "grupo": "catalogos", "descripcion": "Catálogo de segmentos comerciales"},
        {"clave": "catalogo_estatus", "valor": '["PAGADA","AL CORRIENTE","ATRASADA","CANCELADA","PENDIENTE DE PAGO","REHABILITADA"]', "tipo": "json", "grupo": "catalogos", "descripcion": "Catálogo de estatus internos"},
    ]
    for cfg in configs_default:
        db.add(Configuracion(**cfg))

    db.commit()
    print(f"[SEED] {len(polizas_data)} polizas, {len(agentes)} agentes, {len(SEGMENTOS_DEMO)} segmentos, {len(GESTIONES_DEMO)} gestiones insertados.")
    return True
