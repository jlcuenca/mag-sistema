"""
Seed de datos de demostración para MAG Sistema.
Se ejecuta al iniciar la app si la base de datos está vacía.
"""
from sqlalchemy.orm import Session
from .database import SessionLocal, Agente, Producto, Poliza, IndicadorAxa, Meta
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
    {"anio": 2025, "periodo": None, "meta_polizas_vida": 48, "meta_prima_vida": 1_440_000, "meta_polizas_gmm": 240, "meta_asegurados_gmm": 600, "meta_prima_gmm": 5_760_000},
    {"anio": 2025, "periodo": "2025-01", "meta_polizas_vida": 4, "meta_prima_vida": 120_000, "meta_polizas_gmm": 20, "meta_asegurados_gmm": 50, "meta_prima_gmm": 480_000},
]


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
                    "mystatus": "PAGADA TOTAL" if status == "PAGADA" else "CANCELADA CADUCADA",
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
                "mystatus": "PAGADA TOTAL",
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

    # Agentes
    agentes = []
    for a in AGENTES_DEMO:
        ag = Agente(**{k: v for k, v in a.items() if v is not None},
                    promotor="MAG Principal", nombre_promotoria="MAG")
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

    # Metas
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

    db.commit()
    print(f"[SEED] {len(polizas_data)} polizas, {len(agentes)} agentes insertados.")
    return True
