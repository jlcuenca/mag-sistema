"""
Script de reimportación completa de POLIZAS_01_08022026.xlsx
=============================================================
1. Limpia toda la base de datos (drop + create tables)
2. Inserta catálogos base (segmentos, gestiones, configuración)
3. Lee la hoja 'querys' del Excel de referencia
4. Crea agentes y productos automáticamente
5. Inserta todas las pólizas
6. Aplica las reglas de cálculo (motor AUTOMATICO)
"""
import sys
import os
import time

# Agregar el directorio raíz al path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd
from datetime import datetime
from sqlalchemy import text

from api.database import (
    engine, Base, SessionLocal, DB_PATH,
    Segmento, Agente, Producto, Poliza, Meta,
    GestionComercial, Presupuesto, Configuracion, Importacion,
)
from api.rules import (
    normalizar_poliza, calcular_mystatus, es_reexpedicion,
    aplicar_reglas_poliza, aplicar_reglas_batch,
    agrupar_segmento,
)

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════
EXCEL_PATH = os.path.join(ROOT, "ref", "POLIZAS_01_08022026.xlsx")
HOJA = "querys"  # Hoja principal con los datos crudos

# Catálogo de segmentos
SEGMENTOS_CATALOGO = [
    {"nombre": "ALFA TOP INTEGRAL",  "agrupado": "ALFA",  "orden": 1},
    {"nombre": "ALFA TOP COMBINADO", "agrupado": "ALFA",  "orden": 2},
    {"nombre": "ALFA TOP",           "agrupado": "ALFA",  "orden": 3},
    {"nombre": "ALFA INTEGRAL",      "agrupado": "ALFA",  "orden": 4},
    {"nombre": "ALFA/BETA",          "agrupado": "ALFA",  "orden": 5},
    {"nombre": "BETA1",              "agrupado": "BETA",  "orden": 6},
    {"nombre": "BETA2",              "agrupado": "BETA",  "orden": 7},
    {"nombre": "OMEGA",              "agrupado": "OMEGA", "orden": 8},
]

# Gestiones comerciales
GESTIONES_CATALOGO = [
    {"nombre": "ALFA/MARIA ESTHER",   "lider_codigo": "63931", "lider_nombre": "MAG PROMOTORIA", "tipo": "ALFA"},
    {"nombre": "MARIO FLORES",        "lider_codigo": "63931", "lider_nombre": "MAG PROMOTORIA", "tipo": "BETA"},
    {"nombre": "DIRECTA/PROMOTORA",   "lider_codigo": "63931", "lider_nombre": "MAG PROMOTORIA", "tipo": "DIRECTA"},
]

# Configuración del sistema
CONFIGURACION_ITEMS = [
    {"clave": "tc_udis",               "valor": "8.56",   "tipo": "numero",   "grupo": "tipos_cambio",  "descripcion": "Tipo de cambio UDIS a MXN"},
    {"clave": "tc_usd",                "valor": "18.38",  "tipo": "numero",   "grupo": "tipos_cambio",  "descripcion": "Tipo de cambio USD a MXN"},
    {"clave": "anio_analisis",         "valor": "2026",   "tipo": "numero",   "grupo": "general",       "descripcion": "Año de análisis principal"},
    {"clave": "umbral_equiv_2024",     "valor": "15000",  "tipo": "numero",   "grupo": "umbrales",      "descripcion": "Umbral inferior equivalencias 2024"},
    {"clave": "umbral_equiv_2025",     "valor": "16000",  "tipo": "numero",   "grupo": "umbrales",      "descripcion": "Umbral inferior equivalencias 2025+"},
    {"clave": "umbral_equiv_alto",     "valor": "50000",  "tipo": "numero",   "grupo": "umbrales",      "descripcion": "Umbral superior equivalencias"},
    {"clave": "dias_cancelacion",      "valor": "30",     "tipo": "numero",   "grupo": "umbrales",      "descripcion": "Días para marcar cancelación por falta de pago"},
    {"clave": "dias_pendiente",        "valor": "30",     "tipo": "numero",   "grupo": "umbrales",      "descripcion": "Días máximos en pendiente de pago"},
    {"clave": "promotoria_nombre",     "valor": "MAG",    "tipo": "texto",    "grupo": "general",       "descripcion": "Nombre de la promotoría"},
    {"clave": "promotoria_codigo",     "valor": "63931",  "tipo": "texto",    "grupo": "general",       "descripcion": "Código AXA de la promotoría"},
]


def to_float(v):
    """Convierte un valor a float de forma segura."""
    if v is None or pd.isna(v):
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def to_int(v):
    """Convierte un valor a int de forma segura."""
    f = to_float(v)
    return int(f) if f is not None else None


def safe_str(v):
    """Convierte un valor a string seguro, retorna None si vacío/NaN."""
    if v is None:
        return None
    try:
        if isinstance(v, float):
            import math
            if math.isnan(v):
                return None
        s = str(v).strip()
        if s in ("", "None", "nan", "NaN"):
            return None
        return s
    except Exception:
        return None


def main():
    inicio = time.time()
    print("=" * 70)
    print("  MAG Sistema — Reimportación Completa")
    print(f"  Archivo: {EXCEL_PATH}")
    print(f"  BD: {DB_PATH}")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # ═══════════════════════════════════════════════════════════
    # PASO 1: Limpiar la base de datos
    # ═══════════════════════════════════════════════════════════
    print("\n[1/6] Limpiando base de datos...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print(f"  ✅ Tablas recreadas en: {DB_PATH}")

    db = SessionLocal()

    try:
        # ═══════════════════════════════════════════════════════
        # PASO 2: Insertar catálogos base
        # ═══════════════════════════════════════════════════════
        print("\n[2/6] Insertando catálogos base...")

        # Segmentos
        for seg in SEGMENTOS_CATALOGO:
            db.add(Segmento(**seg))
        db.flush()
        print(f"  ✅ {len(SEGMENTOS_CATALOGO)} segmentos")

        # Gestiones comerciales
        for ges in GESTIONES_CATALOGO:
            db.add(GestionComercial(**ges))
        db.flush()
        print(f"  ✅ {len(GESTIONES_CATALOGO)} gestiones comerciales")

        # Configuración
        for cfg in CONFIGURACION_ITEMS:
            db.add(Configuracion(**cfg))
        db.flush()
        print(f"  ✅ {len(CONFIGURACION_ITEMS)} parámetros de configuración")

        db.commit()

        # ═══════════════════════════════════════════════════════
        # PASO 3: Leer el Excel
        # ═══════════════════════════════════════════════════════
        print(f"\n[3/6] Leyendo Excel ({HOJA})...")
        df = pd.read_excel(EXCEL_PATH, sheet_name=HOJA, dtype=str)
        df.columns = [c.strip().upper() for c in df.columns]
        df = df.where(pd.notna(df), None)
        total_filas = len(df)
        print(f"  ✅ {total_filas} filas leídas, {len(df.columns)} columnas")

        # Análisis rápido
        ramos = df["NOMRAMO"].value_counts()
        for ramo, cnt in ramos.items():
            print(f"     • {ramo}: {cnt} pólizas")

        # ═══════════════════════════════════════════════════════
        # PASO 4: Crear agentes y productos
        # ═══════════════════════════════════════════════════════
        print("\n[4/6] Creando agentes y productos...")

        # 4a. Agentes únicos
        agentes_unicos = df["AGENTE"].dropna().unique()
        agente_map = {}  # codigo_agente -> id
        for codigo in agentes_unicos:
            codigo_str = str(codigo).strip()
            if not codigo_str or codigo_str == "None":
                continue
            agente = Agente(
                codigo_agente=codigo_str,
                nombre_completo=f"Agente {codigo_str}",
                nombre_promotoria="MAG",
                situacion="ACTIVO",
            )
            db.add(agente)
            db.flush()
            agente_map[codigo_str] = agente.id
        print(f"  ✅ {len(agente_map)} agentes creados")

        # 4b. Productos únicos
        productos_unicos = {}
        for _, row in df.iterrows():
            ramo_nombre = safe_str(row.get("NOMRAMO")) or ""
            ramo_codigo_str = safe_str(row.get("RAMO")) or ""
            plan = safe_str(row.get("PLAN"))
            gama = safe_str(row.get("GAMA"))

            if not ramo_codigo_str:
                continue
            try:
                ramo_codigo = int(float(ramo_codigo_str))
            except (ValueError, TypeError):
                continue

            key = (ramo_codigo, plan or "", gama or "")
            if key not in productos_unicos:
                productos_unicos[key] = {
                    "ramo_codigo": ramo_codigo,
                    "ramo_nombre": ramo_nombre or f"RAMO {ramo_codigo}",
                    "plan": plan,
                    "gama": gama,
                }

        producto_map = {}  # (ramo_codigo, plan, gama) -> id
        for key, prod_data in productos_unicos.items():
            prod = Producto(**prod_data)
            db.add(prod)
            db.flush()
            producto_map[key] = prod.id
        print(f"  ✅ {len(producto_map)} productos creados")
        db.commit()

        # ═══════════════════════════════════════════════════════
        # PASO 5: Insertar pólizas
        # ═══════════════════════════════════════════════════════
        print(f"\n[5/6] Insertando {total_filas} pólizas...")

        polizas_insertadas = 0
        errores = []
        polizas_para_reglas = []  # Para paso 6

        for i, row in df.iterrows():
            try:
                pol_num = row.get("POLIZA")
                if not pol_num or str(pol_num).strip() == "" or str(pol_num).strip() == "None":
                    continue

                pol_num = str(pol_num).strip()

                # Agente
                agente_codigo = safe_str(row.get("AGENTE")) or ""
                agente_id = agente_map.get(agente_codigo)

                # Producto
                ramo_nombre = safe_str(row.get("NOMRAMO")) or ""
                ramo_codigo_str = safe_str(row.get("RAMO")) or ""
                plan = safe_str(row.get("PLAN"))
                gama = safe_str(row.get("GAMA"))

                try:
                    ramo_codigo = int(float(ramo_codigo_str))
                except (ValueError, TypeError):
                    ramo_codigo = 0

                prod_key = (ramo_codigo, plan or "", gama or "")
                producto_id = producto_map.get(prod_key)

                # Fechas
                fecha_ini = safe_str(row.get("FECINI"))
                if fecha_ini:
                    fecha_ini = fecha_ini[:10]
                fecha_fin = safe_str(row.get("FECFIN"))
                if fecha_fin:
                    fecha_fin = fecha_fin[:10]
                fecha_emi = safe_str(row.get("FECEMI"))
                if fecha_emi:
                    fecha_emi = fecha_emi[:10]

                # Limpiar fechas que no son válidas
                if fecha_ini and len(fecha_ini) < 8:
                    fecha_ini = None
                if fecha_fin and len(fecha_fin) < 8:
                    fecha_fin = None
                if fecha_emi and len(fecha_emi) < 8:
                    fecha_emi = None

                anio = None
                if fecha_ini and len(fecha_ini) >= 4:
                    try:
                        anio = int(fecha_ini[:4])
                    except ValueError:
                        pass

                # Importes
                prima_neta = to_float(row.get("PRIMANETA"))
                prima_total = to_float(row.get("PRIMA_TOT"))
                iva = to_float(row.get("IVA")) or 0
                recargo = to_float(row.get("RECARGO")) or 0
                suma_aseg = to_float(row.get("SUMA"))
                deducible = to_float(row.get("DEDUCIBLE"))
                coaseguro = to_float(row.get("COASEGURO"))
                derecho = to_float(row.get("DERECHO"))
                tope = to_float(row.get("TOPE"))
                num_asegs = to_int(row.get("ASEGS")) or 1

                # Status y moneda
                status = safe_str(row.get("STATUS")) or ""
                moneda = safe_str(row.get("MON")) or "MN"
                mystatus_raw = safe_str(row.get("MYSTATUS")) or ""
                
                # Usar MYSTATUS del Excel como fuente primaria (ya tiene los cálculos correctos)
                # Solo calcular si el Excel no trae MYSTATUS
                if mystatus_raw:
                    mystatus = mystatus_raw
                else:
                    mystatus = calcular_mystatus(
                        status_recibo=status,
                        fecha_emision=fecha_emi,
                        fecha_inicio=fecha_ini,
                    )

                # Nueva/No Nueva del Excel
                nueva_flag_str = (safe_str(row.get("NUEVA")) or "").upper()
                nueva01_str = safe_str(row.get("NUEVA01")) or ""
                es_nueva_val = None
                tipo_poliza = None
                if nueva_flag_str in ("NUEVA", "SI", "1", "TRUE"):
                    es_nueva_val = True
                    tipo_poliza = "NUEVA"
                elif nueva_flag_str in ("NO NUEVA", "NO", "0", "FALSE", "SUBSECUENTE"):
                    es_nueva_val = False
                    tipo_poliza = "SUBSECUENTE"

                # Otros campos
                forma_pago = safe_str(row.get("FP"))
                tipo_pago = safe_str(row.get("TIPPAG"))
                solicitud = safe_str(row.get("SOLICITUD"))
                rfc = safe_str(row.get("RFC"))
                cp = safe_str(row.get("CP"))
                tel = safe_str(row.get("TEL"))
                email = safe_str(row.get("EMAIL"))
                zona = safe_str(row.get("ZONA"))
                red = safe_str(row.get("RED"))
                tabulador = safe_str(row.get("TABULADOR"))
                maternidad = safe_str(row.get("MATERNIDAD"))
                cobertura = safe_str(row.get("COBERTURA"))
                plazo_pago = safe_str(row.get("PLAZOPAGO"))
                notas = safe_str(row.get("NOTA"))
                version = to_int(row.get("VERSION")) or 0

                poliza = Poliza(
                    poliza_original=pol_num,
                    poliza_estandar=normalizar_poliza(pol_num),
                    version=version,
                    solicitud=solicitud,

                    agente_id=agente_id,
                    producto_id=producto_id,

                    asegurado_nombre=safe_str(row.get("ASEGURADO")),
                    contratante_nombre=safe_str(row.get("CONTRATANTE")),
                    rfc=rfc,
                    codigo_postal=cp,
                    telefono=tel,
                    email=email,
                    num_asegurados=num_asegs,

                    fecha_emision=fecha_emi,
                    fecha_inicio=fecha_ini or "2026-01-01",  # fallback
                    fecha_fin=fecha_fin,

                    moneda=moneda,
                    prima_total=prima_total,
                    prima_neta=prima_neta,
                    iva=iva,
                    recargo=recargo,
                    derecho_poliza=derecho,
                    suma_asegurada=suma_aseg,
                    deducible=deducible,
                    coaseguro=coaseguro,
                    forma_pago=forma_pago,
                    tipo_pago=tipo_pago,
                    plazo_pago=plazo_pago,
                    status_recibo=status,
                    gama=gama,
                    tope=tope,
                    zona=zona,
                    red=red,
                    tabulador=tabulador,
                    maternidad=maternidad,
                    cobertura=cobertura,

                    es_nueva=es_nueva_val,
                    tipo_poliza=tipo_poliza,
                    mystatus=mystatus,

                    periodo_aplicacion=f"{anio}-{fecha_ini[5:7]}" if fecha_ini and anio else None,
                    anio_aplicacion=anio,
                    fuente="EXCEL_IMPORT",
                    notas=notas,
                )

                db.add(poliza)
                polizas_insertadas += 1

                # Commit cada 500 para no saturar memoria
                if polizas_insertadas % 500 == 0:
                    db.flush()
                    print(f"     ... {polizas_insertadas} pólizas procesadas")

            except Exception as e:
                errores.append(f"Fila {i + 2}: {str(e)}")
                if len(errores) <= 5:
                    print(f"  ⚠️  Error fila {i + 2}: {str(e)}")
                continue

        db.commit()
        print(f"  ✅ {polizas_insertadas} pólizas insertadas")
        if errores:
            print(f"  ⚠️  {len(errores)} errores (primeros 5 mostrados arriba)")

        # ═══════════════════════════════════════════════════════
        # PASO 6: Aplicar reglas de cálculo
        # ═══════════════════════════════════════════════════════
        print(f"\n[6/6] Aplicando reglas de cálculo a {polizas_insertadas} pólizas...")

        # Leer todas las pólizas con sus datos de producto
        rows = db.execute(text("""
            SELECT p.*, pr.ramo_codigo, pr.ramo_nombre
            FROM polizas p
            LEFT JOIN productos pr ON p.producto_id = pr.id
        """)).mappings().all()

        polizas_dicts = [dict(r) for r in rows]
        print(f"  Procesando {len(polizas_dicts)} pólizas con motor de reglas...")

        resultados = aplicar_reglas_batch(polizas_dicts)
        actualizados = 0
        errores_reglas = []

        for poliza_dict, reglas in zip(polizas_dicts, resultados):
            try:
                db.execute(text("""
                    UPDATE polizas SET
                        largo_poliza = :largo,
                        raiz_poliza_6 = :raiz6,
                        terminacion = :term,
                        num_reexpediciones = :nreexp,
                        id_compuesto = :id_comp,
                        es_reexpedicion = :reexp,
                        primer_anio = :primer,
                        fecha_aplicacion = :fec_apli,
                        mes_aplicacion = :mes_apli,
                        pendientes_pago = :pend,
                        trimestre = :trim,
                        flag_pagada = :fpag,
                        flag_nueva_formal = :fnueva,
                        tipo_poliza = :tipo,
                        prima_anual_pesos = :pap,
                        equivalencias_emitidas = :eqe,
                        equivalencias_pagadas = :eqp,
                        flag_cancelada = :fcanc,
                        prima_proporcional = :pprop,
                        condicional_prima = :cprim,
                        prima_acumulada_basica = :pacum,
                        updated_at = :now
                    WHERE id = :id
                """), {
                    "id": poliza_dict["id"],
                    "largo": reglas["largo_poliza"],
                    "raiz6": reglas["raiz_poliza_6"],
                    "term": reglas["terminacion"],
                    "nreexp": reglas["num_reexpediciones"],
                    "id_comp": reglas["id_compuesto"],
                    "reexp": reglas["es_reexpedicion"],
                    "primer": reglas["primer_anio"],
                    "fec_apli": reglas["fecha_aplicacion"],
                    "mes_apli": reglas["mes_aplicacion"],
                    "pend": reglas["pendientes_pago"],
                    "trim": reglas["trimestre"],
                    "fpag": reglas["flag_pagada"],
                    "fnueva": reglas["flag_nueva_formal"],
                    "tipo": reglas["tipo_poliza_nuevo"],
                    "pap": reglas["prima_anual_pesos"],
                    "eqe": reglas["equivalencias_emitidas"],
                    "eqp": reglas["equivalencias_pagadas"],
                    "fcanc": reglas["flag_cancelada"],
                    "pprop": reglas["prima_proporcional"],
                    "cprim": reglas["condicional_prima"],
                    "pacum": reglas["prima_acumulada_basica"],
                    "now": datetime.now().isoformat(),
                })
                actualizados += 1

                if actualizados % 1000 == 0:
                    db.flush()
                    print(f"     ... {actualizados} reglas aplicadas")

            except Exception as e:
                errores_reglas.append(f"Póliza {poliza_dict.get('poliza_original')}: {str(e)}")
                if len(errores_reglas) <= 3:
                    print(f"  ⚠️  Error regla: {str(e)}")

        db.commit()
        print(f"  ✅ {actualizados} pólizas con reglas aplicadas")

        # ═══════════════════════════════════════════════════════
        # Log de importación
        # ═══════════════════════════════════════════════════════
        log = Importacion(
            tipo="REIMPORTACION_COMPLETA",
            archivo_nombre="POLIZAS_01_08022026.xlsx",
            registros_procesados=total_filas,
            registros_nuevos=polizas_insertadas,
            registros_actualizados=actualizados,
            registros_error=len(errores),
            errores_detalle="\n".join(errores[:20]) if errores else None,
        )
        db.add(log)
        db.commit()

        # ═══════════════════════════════════════════════════════
        # RESUMEN FINAL
        # ═══════════════════════════════════════════════════════
        elapsed = time.time() - inicio

        # Estadísticas
        total_pol = db.execute(text("SELECT COUNT(*) FROM polizas")).scalar()
        total_agentes = db.execute(text("SELECT COUNT(*) FROM agentes")).scalar()
        total_productos = db.execute(text("SELECT COUNT(*) FROM productos")).scalar()

        # Por ramo
        ramos_stats = db.execute(text("""
            SELECT pr.ramo_nombre, COUNT(*) as cnt,
                   ROUND(SUM(COALESCE(p.prima_neta, 0)), 2) as prima_total
            FROM polizas p
            JOIN productos pr ON p.producto_id = pr.id
            GROUP BY pr.ramo_nombre
            ORDER BY cnt DESC
        """)).mappings().all()

        # Por año
        anios_stats = db.execute(text("""
            SELECT anio_aplicacion, COUNT(*) as cnt
            FROM polizas
            WHERE anio_aplicacion IS NOT NULL
            GROUP BY anio_aplicacion
            ORDER BY anio_aplicacion
        """)).mappings().all()

        # Status
        status_stats = db.execute(text("""
            SELECT mystatus, COUNT(*) as cnt
            FROM polizas
            GROUP BY mystatus
            ORDER BY cnt DESC
            LIMIT 10
        """)).mappings().all()

        print("\n" + "=" * 70)
        print("  RESUMEN DE IMPORTACIÓN")
        print("=" * 70)
        print(f"  ⏱  Tiempo total:        {elapsed:.1f} segundos")
        print(f"  📊 Pólizas en BD:        {total_pol}")
        print(f"  👤 Agentes:              {total_agentes}")
        print(f"  📦 Productos:            {total_productos}")
        print(f"  ❌ Errores importación:   {len(errores)}")
        print(f"  ❌ Errores reglas:        {len(errores_reglas)}")

        print("\n  Por Ramo:")
        for r in ramos_stats:
            print(f"     • {r['ramo_nombre']}: {r['cnt']} pólizas — "
                  f"${r['prima_total']:,.0f} MXN prima neta")

        print("\n  Por Año:")
        for a in anios_stats:
            print(f"     • {a['anio_aplicacion']}: {a['cnt']} pólizas")

        print("\n  Por Status (MyStatus):")
        for s in status_stats:
            print(f"     • {s['mystatus'] or '(vacío)'}: {s['cnt']}")

        print("\n" + "=" * 70)
        print("  ✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
