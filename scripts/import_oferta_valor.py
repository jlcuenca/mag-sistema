"""
Script de importación: Oferta de Valor AXA (xlsb) → indicadores_axa + conciliación
Lee la hoja 'sabana' y la hoja 'detalle_pol'.

Uso:
    python scripts/import_oferta_valor.py ref/Oferta_valor_12_63931.xlsb --periodo 2025-12
"""
import os, sys, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyxlsb import open_workbook
from sqlalchemy import text
from api.database import SessionLocal, IndicadorAxa, Importacion

# ─── Mapa correcto: columnas 0-121 (fila 1 = headers cortos) ────
# Row 1: agente(0), agts(1), nombre_com(2), rol(3), situacion(4),
#         fec_alta(5), fec_rehab(6), fec_cancel(7), causa_can(8),
#         territorio(9), oficina(10), gerencia(11), promotor(12),
#         nom_prom(13), cc(14), desc_cc(15), identifica(16),
#         cve_agrup(17), nom_agrup(18), canal(19), cc_tit(20),
#         seg_act(21), recproa(22), recprob(23), recpro(24),
#         equi_vi(25), polvinn(26), pmavi1a(27),
#         alfa_ant(28), alfa_act(29),
#         pol_gm(30), pol_pm(31), pma_pag_pm(32),
#         aseg_nvos(33), pmagm1aind(34),
#         pma_com_ai(35), pma_com_hi(36),
#         pc_lp_ant(37), pc_lp_act(38),
#         vida_act(39), salud_act(40),
#         bono_bic(41), anio_rp(42),
#         cnagb_ant(43), cnagb_a(44), cnagb_b(45), cnagb(46),
#         arranque(47), bono_mes(48), bono_trim(49),
#         rk_pag(50), ...
#         mdc(94), semsa(100), id_mdrt(101), participa(102), estatus(103),
#         meta_tot(113), cump_tot(114), falta_tot(115)

COL = {
    "agente": 0,         # Código agente
    "nombre": 2,         # Nombre Completo
    "rol": 3,            # Rol
    "situacion": 4,      # Situación
    "territorio": 9,     # Territorio
    "oficina": 10,       # Oficina
    "gerencia": 11,      # Gerencia
    "promotor": 12,      # Promotor
    "nom_prom": 13,      # Nombre Promotoría
    "cc_tit": 20,        # CC Titular
    "segmento": 21,      # seg_act — Segmento Corriente
    # Producción Vida
    "equiv_vida": 25,    # equi_vi — Equivalencias Vida
    "polizas_vida": 26,  # polvinn — Pólizas Vida Nuevo Negocio
    "prima_vida_1er": 27, # pmavi1a — Prima Pagada Vida 1er Año
    "alfa_ant": 28,      # alfa_ant
    "alfa_act": 29,      # alfa_act
    # Producción GMM
    "polizas_gmm": 30,   # pol_gm
    "polizas_planmed": 31, # pol_pm
    "prima_planmed": 32, # pma_pag_pm
    "asegurados": 33,    # aseg_nvos
    "prima_gmm_1er": 34, # pmagm1aind
    # Autos/LP
    "prima_autos": 35,   # pma_com_ai — Prima Computable Autos Individual
    "prima_hogar": 36,   # pma_com_hi
    "prima_lp_ant": 37,  # pc_lp_ant
    "prima_lp_act": 38,  # pc_lp_act
    # Totales
    "prima_vida_act": 39, # vida_act
    "prima_salud_act": 40, # salud_act
    # Incentivos
    "bono_bic": 41,
    "congreso_beta": 46, # cnagb
    "arranque": 47,
    "bono_mes": 48,
    "bono_trim": 49,
    "mdc": 94,           # Mesa de Campeones
    "semsa": 100,        # Seminario de Salud
    "mdrt_id": 101,
    "mdrt_participa": 102,
    "mdrt_estatus": 103,
    "meta_mdrt": 113,    # meta_tot
    "alcance_mdrt": 114, # cump_tot
    "faltante_mdrt": 115, # falta_tot
    "persistencia": 89,  # persis
    "recluta_prod": 24,  # recpro
}


def safe_float(v):
    if v is None: return 0.0
    try: return float(v)
    except: return 0.0

def safe_str(v):
    if v is None: return None
    s = str(v).strip()
    return s if s else None

def safe_int(v):
    try: return int(float(v)) if v is not None else 0
    except: return 0

def agent_code(v):
    """Convierte código agente a string limpio."""
    if v is None: return None
    try: return str(int(float(v)))
    except: return str(v).strip()


def import_sabana(filepath: str, periodo: str, db):
    """Importa hoja sabana → indicadores por agente."""
    print(f"\n📊 Importando sabana de {os.path.basename(filepath)}...")
    
    agentes = 0
    errores = []
    
    with open_workbook(filepath) as wb:
        if "sabana" not in wb.sheets:
            return 0, ["Hoja 'sabana' no encontrada"]
        
        with wb.get_sheet("sabana") as sheet:
            skip_header = True
            
            for row_idx, row in enumerate(sheet.rows()):
                values = [item.v for item in row]
                
                # Fila 0 = IDs numéricos (headers de display)
                # Fila 1 = nombres cortos (headers de datos)
                if row_idx <= 1:
                    continue
                
                try:
                    def get(key):
                        idx = COL.get(key, -1)
                        return values[idx] if 0 <= idx < len(values) else None
                    
                    codigo = agent_code(get("agente"))
                    if not codigo:
                        continue
                    
                    nombre = safe_str(get("nombre"))
                    if not nombre:
                        continue
                    
                    # Producción
                    equiv = safe_float(get("equiv_vida"))
                    pol_vida = safe_int(get("polizas_vida"))
                    prima_vida = safe_float(get("prima_vida_1er"))
                    pol_gmm = safe_int(get("polizas_gmm"))
                    aseg = safe_int(get("asegurados"))
                    prima_gmm = safe_float(get("prima_gmm_1er"))
                    prima_autos = safe_float(get("prima_autos"))
                    segmento = safe_str(get("segmento"))
                    alfa_ant = safe_str(get("alfa_ant"))
                    alfa_act = safe_str(get("alfa_act"))
                    
                    # Incentivos resumidos
                    incentivos = []
                    if safe_str(get("bono_bic")): incentivos.append(f"BIC={get('bono_bic')}")
                    if safe_str(get("congreso_beta")): incentivos.append(f"CongBeta={get('congreso_beta')}")
                    if safe_str(get("mdc")): incentivos.append(f"MdC={get('mdc')}")
                    if safe_str(get("semsa")): incentivos.append(f"SemSa={get('semsa')}")
                    if safe_str(get("mdrt_estatus")): incentivos.append(f"MDRT={get('mdrt_estatus')}")
                    if safe_str(get("recluta_prod")): incentivos.append(f"RP={get('recluta_prod')}")
                    inc_str = "|".join(incentivos) if incentivos else None
                    
                    extras = f"seg={segmento}|alfa_ant={alfa_ant}|alfa_act={alfa_act}"
                    if inc_str:
                        extras += f"|{inc_str}"
                    
                    # Insertar Vida
                    if pol_vida > 0 or prima_vida > 0 or equiv > 0:
                        db.execute(text("""
                            INSERT INTO indicadores_axa (
                                periodo, poliza, agente_codigo, ramo,
                                num_asegurados, polizas_equivalentes, prima_primer_anio,
                                es_nueva_axa, encontrada_en_base, diferencia_clasificacion
                            ) VALUES (:per, :pol, :agc, 'VIDA', 1, :peq, :ppa, true, true, :dif)
                        """), {
                            "per": periodo,
                            "pol": f"OV-VIDA-{codigo}",
                            "agc": codigo,
                            "peq": equiv,
                            "ppa": prima_vida,
                            "dif": extras,
                        })
                    
                    # Insertar GMM
                    if pol_gmm > 0 or prima_gmm > 0 or aseg > 0:
                        db.execute(text("""
                            INSERT INTO indicadores_axa (
                                periodo, poliza, agente_codigo, ramo,
                                num_asegurados, polizas_equivalentes, prima_primer_anio,
                                es_nueva_axa, encontrada_en_base, diferencia_clasificacion
                            ) VALUES (:per, :pol, :agc, 'GMM', :nas, :peq, :ppa, true, true, :dif)
                        """), {
                            "per": periodo,
                            "pol": f"OV-GMM-{codigo}",
                            "agc": codigo,
                            "nas": aseg,
                            "peq": pol_gmm,
                            "ppa": prima_gmm,
                            "dif": extras,
                        })
                    
                    # Insertar Autos
                    if prima_autos > 0:
                        db.execute(text("""
                            INSERT INTO indicadores_axa (
                                periodo, poliza, agente_codigo, ramo,
                                num_asegurados, polizas_equivalentes, prima_primer_anio,
                                es_nueva_axa, encontrada_en_base, diferencia_clasificacion
                            ) VALUES (:per, :pol, :agc, 'AUTOS', 1, 0, :ppa, true, true, :dif)
                        """), {
                            "per": periodo,
                            "pol": f"OV-AUTOS-{codigo}",
                            "agc": codigo,
                            "ppa": prima_autos,
                            "dif": extras,
                        })
                    
                    agentes += 1
                    
                except Exception as e:
                    errores.append(f"Fila {row_idx+1}: {e}")
                    if len(errores) <= 3:
                        print(f"  ⚠️ {errores[-1]}")
    
    print(f"  ✅ Sabana: {agentes} agentes procesados, {len(errores)} errores")
    return agentes, errores


def import_detalle_pol(filepath: str, periodo: str, db):
    """Importa hoja detalle_pol → indicadores por póliza."""
    print(f"\n📋 Importando detalle_pol...")
    
    count = 0
    no_encontradas = 0
    errores = []
    
    with open_workbook(filepath) as wb:
        if "detalle_pol" not in wb.sheets:
            return 0, ["Hoja 'detalle_pol' no encontrada"]
        
        with wb.get_sheet("detalle_pol") as sheet:
            for row_idx, row in enumerate(sheet.rows()):
                values = [item.v for item in row]
                
                if row_idx == 0:  # header
                    continue
                
                try:
                    poliza = safe_str(values[0])
                    if not poliza:
                        continue
                    
                    agente = agent_code(values[1])
                    ramo = safe_str(values[9])
                    cnt = safe_int(values[10])
                    vigente = safe_str(values[11]) if len(values) > 11 else None
                    
                    # Verificar en base interna
                    from api.rules import normalizar_poliza
                    pol_norm = normalizar_poliza(poliza)
                    encontrada = db.execute(
                        text("SELECT id FROM polizas WHERE poliza_estandar=:pe OR poliza_original=:po"),
                        {"pe": pol_norm, "po": poliza}
                    ).scalar()
                    
                    if not encontrada:
                        no_encontradas += 1
                    
                    db.execute(text("""
                        INSERT INTO indicadores_axa (
                            periodo, poliza, agente_codigo, ramo,
                            num_asegurados, es_nueva_axa, encontrada_en_base,
                            diferencia_clasificacion
                        ) VALUES (:per, :pol, :agc, :ram, :nas, true, :enb, :dif)
                    """), {
                        "per": periodo,
                        "pol": poliza,
                        "agc": agente,
                        "ram": ramo,
                        "nas": cnt,
                        "enb": True if encontrada else False,
                        "dif": f"vigente={vigente}" if not encontrada else None,
                    })
                    
                    count += 1
                    if count % 5000 == 0:
                        db.flush()
                        print(f"  ... {count} pólizas procesadas")
                    
                except Exception as e:
                    errores.append(f"Fila {row_idx+1}: {e}")
    
    print(f"  ✅ Detalle_pol: {count} pólizas, {no_encontradas} no encontradas, {len(errores)} errores")
    return count, errores


def run_conciliacion(periodo: str, db):
    """Resumen de conciliación."""
    print(f"\n🔄 Conciliación AXA — Periodo {periodo}")
    print(f"{'─'*50}")
    
    # Pólizas
    r = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN encontrada_en_base = true THEN 1 ELSE 0 END) as ok,
            SUM(CASE WHEN encontrada_en_base = false THEN 1 ELSE 0 END) as missing,
            COUNT(DISTINCT agente_codigo) as agentes
        FROM indicadores_axa
        WHERE periodo = :per AND poliza NOT LIKE 'OV-%'
    """), {"per": periodo}).mappings().first()
    
    if r and r["total"]:
        pct = round(int(r["ok"] or 0) / max(int(r["total"]), 1) * 100, 1)
        print(f"  Pólizas AXA:     {r['total']}")
        print(f"  ✅ Encontradas:  {r['ok']}")
        print(f"  ❌ No encontradas: {r['missing']}")
        print(f"  📊 Coincidencia: {pct}%")
        print(f"  👥 Agentes:      {r['agentes']}")
    
    # Indicadores por agente
    r2 = db.execute(text("""
        SELECT ramo, COUNT(*) as n,
               SUM(COALESCE(prima_primer_anio, 0)) as prima,
               SUM(COALESCE(polizas_equivalentes, 0)) as equiv,
               SUM(COALESCE(num_asegurados, 0)) as aseg
        FROM indicadores_axa
        WHERE periodo = :per AND poliza LIKE 'OV-%'
        GROUP BY ramo
    """), {"per": periodo}).mappings().all()
    
    if r2:
        print(f"\n  Indicadores Oferta de Valor (agente):")
        for row in r2:
            print(f"    {row['ramo']:8s}: {row['n']} agentes, "
                  f"Prima=${row['prima']:,.0f}, "
                  f"Equiv={row['equiv']:.1f}, Aseg={row['aseg']}")


def main():
    parser = argparse.ArgumentParser(description="Importar Oferta de Valor AXA")
    parser.add_argument("archivo", help="Ruta al archivo xlsb")
    parser.add_argument("--periodo", required=True, help="Periodo YYYY-MM")
    parser.add_argument("--solo-sabana", action="store_true")
    parser.add_argument("--solo-detalle", action="store_true")
    parser.add_argument("--limpiar", action="store_true", help="Limpiar periodo antes")
    args = parser.parse_args()
    
    if not os.path.exists(args.archivo):
        print(f"❌ {args.archivo} no encontrado")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        if args.limpiar:
            n = db.execute(text("DELETE FROM indicadores_axa WHERE periodo=:p"), {"p": args.periodo}).rowcount
            db.commit()
            print(f"🗑️ {n} registros eliminados del periodo {args.periodo}")
        
        total = 0
        all_errors = []
        
        if not args.solo_detalle:
            n, errs = import_sabana(args.archivo, args.periodo, db)
            total += n
            all_errors.extend(errs)
        
        if not args.solo_sabana:
            n, errs = import_detalle_pol(args.archivo, args.periodo, db)
            total += n
            all_errors.extend(errs)
        
        db.commit()
        
        # Log
        db.add(Importacion(
            tipo="OFERTA_VALOR_AXA",
            archivo_nombre=os.path.basename(args.archivo),
            registros_procesados=total,
            registros_nuevos=total,
            registros_error=len(all_errors),
            errores_detalle="\n".join(all_errors[:20]) if all_errors else None,
        ))
        db.commit()
        
        run_conciliacion(args.periodo, db)
        
        print(f"\n{'='*50}")
        print(f"✅ Importación completada: {total} registros")
        if all_errors:
            print(f"⚠️ {len(all_errors)} errores")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
