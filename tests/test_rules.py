"""
Tests de verificación — Motor de reglas MAG-AXA
=================================================
Cubre todas las funciones de rules.py (R1–R7 + columnas AUTOMATICO BG–CW)
y el orquestador aplicar_reglas_poliza / aplicar_reglas_batch.

Ejecutar: python -m pytest tests/test_rules.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════
# Importamos todas las funciones bajo prueba
# ══════════════════════════════════════════════════════════════════
from api.rules import (
    # Reglas originales R1–R7
    clasificar_poliza,
    es_asegurado_nuevo_gmm,
    alerta_frontera_anio,
    es_reexpedicion,
    extraer_raiz_poliza,
    calcular_mystatus,
    normalizar_poliza,
    agrupar_segmento,
    mapear_estatus_cubo,
    clasificar_cy,
    calcular_kpis_polizas,
    # Columnas AUTOMATICO (BG–CW)
    largo_poliza,
    raiz_poliza_6,
    terminacion_poliza,
    generar_id_compuesto,
    determinar_primer_anio,
    mes_aplicacion,
    detectar_pendientes_pago,
    calcular_trimestre,
    flag_pagada,
    flag_nueva_formal,
    prima_anual_en_pesos,
    calcular_equivalencias,
    calcular_equivalencias_pagadas,
    flag_cancelada,
    prima_proporcional,
    condicional_prima,
    # Orquestador
    aplicar_reglas_poliza,
    aplicar_reglas_batch,
    # Constantes
    CATALOGO_ESTATUS,
    ESTATUS_CUBO_MAP,
    SEGMENTOS,
    ESTATUS_CANCELADA,
    TC_UDIS,
    TC_USD,
    # Fase 3
    construir_cadena_renovaciones,
    calcular_faltantes,
)


# ══════════════════════════════════════════════════════════════════
# R1+R2: clasificar_poliza
# ══════════════════════════════════════════════════════════════════

class TestClasificarPoliza:
    """Reglas 1 y 2: Nueva/Subsecuente + Prima Básica/Excedente."""

    def test_gmm_nueva_pagada_2025(self):
        r = clasificar_poliza(34, "2025-03-01", "PAGADA", 2025)
        assert r["tipo_poliza"] == "NUEVA"
        assert r["es_nueva"] is True

    def test_gmm_nueva_poliza_pagada_variant(self):
        """El estatus del cubo 'POLIZA PAGADA' también debe contar como pagada."""
        r = clasificar_poliza(34, "2025-06-01", "POLIZA PAGADA", 2025)
        assert r["tipo_poliza"] == "NUEVA"

    def test_gmm_subsecuente(self):
        r = clasificar_poliza(34, "2024-06-01", "PAGADA", 2025)
        assert r["tipo_poliza"] == "SUBSECUENTE"
        assert r["es_nueva"] is False

    def test_gmm_no_aplica_anio_viejo(self):
        r = clasificar_poliza(34, "2022-01-01", "PAGADA", 2025)
        assert r["tipo_poliza"] == "NO_APLICA"

    def test_gmm_no_aplica_no_pagada(self):
        r = clasificar_poliza(34, "2025-06-01", "CANCELADA", 2025)
        assert r["tipo_poliza"] == "NO_APLICA"

    def test_vida_nueva_basica(self):
        r = clasificar_poliza(11, "2025-03-01", "PAGADA", 2025,
                              prima_neta=10000, comision=300)
        assert r["tipo_poliza"] == "NUEVA"
        assert r["tipo_prima"] == "BASICA"
        assert r["pct_comision"] == pytest.approx(0.03, abs=0.001)

    def test_vida_excedente(self):
        """Comisión < 2.1% → EXCEDENTE, no cuenta como NUEVA."""
        r = clasificar_poliza(11, "2025-03-01", "PAGADA", 2025,
                              prima_neta=10000, comision=100)
        assert r["tipo_prima"] == "EXCEDENTE"
        assert r["tipo_poliza"] == "NO_APLICA"

    def test_vida_subsecuente(self):
        r = clasificar_poliza(11, "2024-03-01", "PAGADA", 2025,
                              prima_neta=10000, comision=300)
        assert r["tipo_poliza"] == "SUBSECUENTE"

    def test_sin_fecha_inicio(self):
        r = clasificar_poliza(34, "", "PAGADA", 2025)
        assert r["tipo_poliza"] == "NO_APLICA"


# ══════════════════════════════════════════════════════════════════
# R3: Asegurado nuevo GMM
# ══════════════════════════════════════════════════════════════════

class TestAseguradoNuevoGMM:
    def test_nuevo(self):
        assert es_asegurado_nuevo_gmm(True, False, "2025-06-01", "2025-06-01") is True

    def test_con_reconocimiento_antiguedad(self):
        assert es_asegurado_nuevo_gmm(True, True, "2025-06-01", "2025-06-01") is False

    def test_no_pagada(self):
        assert es_asegurado_nuevo_gmm(False, False, "2025-06-01", "2025-06-01") is False

    def test_fechas_distintas(self):
        assert es_asegurado_nuevo_gmm(True, False, "2024-01-01", "2025-06-01") is False


# ══════════════════════════════════════════════════════════════════
# R4: Frontera de año
# ══════════════════════════════════════════════════════════════════

class TestAlertaFronteraAnio:
    @pytest.mark.parametrize("fecha,esperado", [
        ("2025-01-02", True),
        ("2025-01-05", True),
        ("2025-01-01", False),  # 1 de enero no entra
        ("2025-01-06", False),
        ("2025-06-03", False),
        ("", False),
        (None, False),
    ])
    def test_frontera(self, fecha, esperado):
        assert alerta_frontera_anio(fecha) == esperado


# ══════════════════════════════════════════════════════════════════
# R5: Reexpediciones
# ══════════════════════════════════════════════════════════════════

class TestReexpedicion:
    def test_original(self):
        assert es_reexpedicion("0076384A00") is False

    def test_reexpedida(self):
        assert es_reexpedicion("0076384A01") is True
        assert es_reexpedicion("0076384A02") is True

    def test_vacio(self):
        assert es_reexpedicion("") is False
        assert es_reexpedicion(None) is False

    def test_extraer_raiz(self):
        assert extraer_raiz_poliza("0076384A01") == "0076384A"

    def test_extraer_raiz_sin_terminacion(self):
        # Si termina en caracteres no numéricos, devuelve tal cual
        assert extraer_raiz_poliza("POLIZAABC") == "POLIZAABC"


# ══════════════════════════════════════════════════════════════════
# R6: MYSTATUS
# ══════════════════════════════════════════════════════════════════

class TestCalcularMystatus:
    def test_cubo_pagada(self):
        assert calcular_mystatus("", "POLIZA PAGADA") == "PAGADA"

    def test_cubo_cancelada_falta_pago(self):
        assert calcular_mystatus("", "POLIZA CANCELADA", "FALTA DE PAGO") == "CANCELADA CADUCADA"

    def test_cubo_cancelada_no_tomada(self):
        assert calcular_mystatus("", "POLIZA CANCELADA", "NO TOMADA") == "CANCELADA NO TOMADA"

    def test_cubo_cancelada_sustitucion(self):
        assert calcular_mystatus("", "POLIZA CANCELADA", "SUSTITUCION") == "CANCELADA POR SUSTITUCION"

    def test_cubo_cancelada_sin_detalle(self):
        assert calcular_mystatus("", "POLIZA CANCELADA") == "CANCELADA"

    def test_cubo_al_corriente(self):
        assert calcular_mystatus("", "POLIZA AL CORRIENTE") == "AL CORRIENTE"

    def test_cubo_rehabilitada(self):
        assert calcular_mystatus("", "POLIZA REHABILITADA") == "REHABILITADA"

    def test_fallback_canc_fpago(self):
        assert calcular_mystatus("CANC/X F.PAGO") == "CANCELADA CADUCADA"

    def test_fallback_pagada(self):
        assert calcular_mystatus("PAGADA") == "PAGADA"


# ══════════════════════════════════════════════════════════════════
# R7: Normalización
# ══════════════════════════════════════════════════════════════════

class TestNormalizarPoliza:
    @pytest.mark.parametrize("entrada,esperado", [
        ("0076384A", "76384A"),
        ("00123U00", "123U00"),
        ("76384A", "76384A"),
        ("", ""),
        (None, None),
    ])
    def test_normalizar(self, entrada, esperado):
        assert normalizar_poliza(entrada) == esperado


# ══════════════════════════════════════════════════════════════════
# Segmentos
# ══════════════════════════════════════════════════════════════════

class TestAgruparSegmento:
    @pytest.mark.parametrize("segmento,esperado", [
        ("ALFA TOP INTEGRAL", "ALFA"),
        ("ALFA TOP COMBINADO", "ALFA"),
        ("ALFA TOP", "ALFA"),
        ("ALFA INTEGRAL", "ALFA"),
        ("ALFA/BETA", "ALFA"),
        ("BETA1", "BETA"),
        ("BETA2", "BETA"),
        ("OMEGA", "OMEGA"),
        ("DESCONOCIDO", "OMEGA"),
        ("", "OMEGA"),
        (None, "OMEGA"),
    ])
    def test_agrupamiento(self, segmento, esperado):
        assert agrupar_segmento(segmento) == esperado


# ══════════════════════════════════════════════════════════════════
# Mapeo estatus cubo
# ══════════════════════════════════════════════════════════════════

class TestMapearEstatusCubo:
    @pytest.mark.parametrize("cubo,esperado", [
        ("POLIZA PAGADA", "PAGADA"),
        ("POLIZA AL CORRIENTE", "AL CORRIENTE"),
        ("POLIZA CANCELADA", "CANCELADA"),
        ("POLIZA ATRASADA", "ATRASADA"),
        ("POLIZA PENDIENTE", "PENDIENTE DE PAGO"),
        ("POLIZA REHABILITADA", "REHABILITADA"),
        ("POLIZA NO TOMADA", "NO TOMADA"),
        ("", ""),
        (None, ""),
    ])
    def test_mapeo(self, cubo, esperado):
        assert mapear_estatus_cubo(cubo) == esperado


# ══════════════════════════════════════════════════════════════════
# Clasificación CY
# ══════════════════════════════════════════════════════════════════

class TestClasificarCY:
    def test_subsecuente(self):
        r = clasificar_cy("CY SUBSECUENTE")
        assert r["tipo_poliza"] == "SUBSECUENTE"
        assert r["es_nueva"] is False

    def test_anual(self):
        r = clasificar_cy("CY ANUAL")
        assert r["tipo_poliza"] == "NUEVA"
        assert r["es_nueva"] is True

    def test_nulo(self):
        r = clasificar_cy(None)
        assert r["tipo_poliza"] == "NO_APLICA"


# ══════════════════════════════════════════════════════════════════
# BG: LARGO POLIZA
# ══════════════════════════════════════════════════════════════════

class TestLargoPoliza:
    def test_normal(self):
        assert largo_poliza("0076384A00") == 10

    def test_6_chars(self):
        assert largo_poliza("12345V") == 6

    def test_vacio(self):
        assert largo_poliza("") == 0
        assert largo_poliza(None) == 0


# ══════════════════════════════════════════════════════════════════
# BH: RAIZ POLIZA 6
# ══════════════════════════════════════════════════════════════════

class TestRaizPoliza6:
    def test_normal(self):
        assert raiz_poliza_6("0076384A00") == "007638"

    def test_corta(self):
        assert raiz_poliza_6("ABC") == "ABC"

    def test_vacio(self):
        assert raiz_poliza_6("") == ""
        assert raiz_poliza_6(None) == ""


# ══════════════════════════════════════════════════════════════════
# BI: TERMINACIÓN
# ══════════════════════════════════════════════════════════════════

class TestTerminacionPoliza:
    def test_normal(self):
        assert terminacion_poliza("0076384A00") == "00"

    def test_reexpedida(self):
        assert terminacion_poliza("0076384A01") == "01"

    def test_con_letra(self):
        assert terminacion_poliza("12345V") == "5V"

    def test_vacio(self):
        assert terminacion_poliza("") == ""
        assert terminacion_poliza(None) == ""


# ══════════════════════════════════════════════════════════════════
# BT: ID COMPUESTO
# ══════════════════════════════════════════════════════════════════

class TestIdCompuesto:
    def test_normal(self):
        assert generar_id_compuesto("17958V00", "2025-01-15") == "17958V002025-01-15"

    def test_vacios(self):
        assert generar_id_compuesto("", "") == ""
        assert generar_id_compuesto(None, None) == ""


# ══════════════════════════════════════════════════════════════════
# BJ: PRIMER AÑO
# ══════════════════════════════════════════════════════════════════

class TestDeterminarPrimerAnio:
    def test_datos_fijos(self):
        r = determinar_primer_anio("17958V00", "2025-01-15", 2025,
                                   datos_fijos_primer_anio="PRIMER AÑO 2023")
        assert r == "PRIMER AÑO 2023"

    def test_indicadores(self):
        r = determinar_primer_anio("17958V00", "2025-01-15", 2025,
                                   poliza_en_indicadores={2024: True})
        assert r == "PRIMER AÑO 2024"

    def test_fecha_aplicacion(self):
        r = determinar_primer_anio("17958V00", "2025-01-15", 2025,
                                   fecha_aplicacion="2025-03-01")
        assert r == "PRIMER AÑO 2025"

    def test_2026_pendiente(self):
        r = determinar_primer_anio("17958V00", "2026-01-15", 2026)
        assert "2026" in r
        assert "PENDIENTE" in r

    def test_sin_datos(self):
        r = determinar_primer_anio("", "", 2020)
        assert r == "-"


# ══════════════════════════════════════════════════════════════════
# BL: MES APLICACIÓN
# ══════════════════════════════════════════════════════════════════

class TestMesAplicacion:
    @pytest.mark.parametrize("fecha,esperado", [
        ("2025-01-15", "ENERO"),
        ("2025-06-01", "JUNIO"),
        ("2025-12-31", "DICIEMBRE"),
        ("-", ""),
        ("", ""),
        (None, ""),
    ])
    def test_mes(self, fecha, esperado):
        assert mes_aplicacion(fecha) == esperado


# ══════════════════════════════════════════════════════════════════
# CA: TRIMESTRE
# ══════════════════════════════════════════════════════════════════

class TestCalcularTrimestre:
    @pytest.mark.parametrize("fecha,esperado", [
        ("2025-01-15", "Q1"),
        ("2025-03-31", "Q1"),
        ("2025-04-01", "Q2"),
        ("2025-06-30", "Q2"),
        ("2025-07-01", "Q3"),
        ("2025-09-30", "Q3"),
        ("2025-10-01", "Q4"),
        ("2025-12-31", "Q4"),
        ("-", "-"),
        ("", "-"),
    ])
    def test_trimestre_fecha(self, fecha, esperado):
        assert calcular_trimestre(fecha) == esperado

    def test_trimestre_por_nombre_mes(self):
        assert calcular_trimestre("ENERO") == "Q1"
        assert calcular_trimestre("JULIO") == "Q3"
        assert calcular_trimestre("DICIEMBRE") == "Q4"


# ══════════════════════════════════════════════════════════════════
# CI: FLAG PAGADA
# ══════════════════════════════════════════════════════════════════

class TestFlagPagada:
    def test_pagada(self):
        assert flag_pagada("2025-03-01") == 1

    def test_no_pagada_guion(self):
        assert flag_pagada("-") == 0

    def test_no_pagada_vacio(self):
        assert flag_pagada("") == 0
        assert flag_pagada(None) == 0


# ══════════════════════════════════════════════════════════════════
# CM: PRIMA ANUAL EN PESOS
# ══════════════════════════════════════════════════════════════════

class TestPrimaAnualEnPesos:
    def test_mn(self):
        assert prima_anual_en_pesos(10000.0, "MN") == 10000.0

    def test_udis(self):
        assert prima_anual_en_pesos(1000.0, "UDIS") == pytest.approx(1000 * TC_UDIS, abs=0.01)

    def test_usd(self):
        assert prima_anual_en_pesos(1000.0, "USD") == pytest.approx(1000 * TC_USD, abs=0.01)

    def test_dls_variant(self):
        assert prima_anual_en_pesos(1000.0, "DLS") == pytest.approx(1000 * TC_USD, abs=0.01)

    def test_cero(self):
        assert prima_anual_en_pesos(0, "MN") == 0.0
        assert prima_anual_en_pesos(None, "MN") == 0.0


# ══════════════════════════════════════════════════════════════════
# CN: EQUIVALENCIAS EMITIDAS
# ══════════════════════════════════════════════════════════════════

class TestEquivalencias:
    def test_cero(self):
        assert calcular_equivalencias(0, 2025) == 0.0

    def test_baja_2024(self):
        """< 15000 en 2024 → 0.5"""
        assert calcular_equivalencias(14999, 2024) == 0.5

    def test_baja_2025(self):
        """< 16000 en 2025 → 0.5"""
        assert calcular_equivalencias(15999, 2025) == 0.5

    def test_media(self):
        """16000 ≤ prima < 50000 → 1.0"""
        assert calcular_equivalencias(30000, 2025) == 1.0

    def test_alta(self):
        """≥ 50000 → 2.0"""
        assert calcular_equivalencias(50000, 2025) == 2.0
        assert calcular_equivalencias(100000, 2025) == 2.0


# ══════════════════════════════════════════════════════════════════
# CO: EQUIVALENCIAS PAGADAS
# ══════════════════════════════════════════════════════════════════

class TestEquivalenciasPagadas:
    def test_cancelada_devuelve_cero(self):
        assert calcular_equivalencias_pagadas(30000, 10000, 2025, 0, "2025-03-01") == 0.0

    def test_sin_fecha_apli(self):
        assert calcular_equivalencias_pagadas(30000, 10000, 2025, 1, "-") == 0.0
        assert calcular_equivalencias_pagadas(30000, 10000, 2025, 1, None) == 0.0

    def test_sin_prima_acum(self):
        assert calcular_equivalencias_pagadas(30000, 0, 2025, 1, "2025-03-01") == 0.0

    def test_normal(self):
        assert calcular_equivalencias_pagadas(30000, 10000, 2025, 1, "2025-03-01") == 1.0


# ══════════════════════════════════════════════════════════════════
# CP: FLAG CANCELADA
# ══════════════════════════════════════════════════════════════════

class TestFlagCancelada:
    def test_cancelada(self):
        assert flag_cancelada("CANCELADA NO TOMADA") == 0
        assert flag_cancelada("CANCELADA CADUCADA") == 0
        assert flag_cancelada("CANC/X F.PAGO") == 0
        assert flag_cancelada("CANCELADA") == 0

    def test_vigente(self):
        assert flag_cancelada("PAGADA TOTAL") == 1
        assert flag_cancelada("AL CORRIENTE") == 1

    def test_sin_estatus_con_prima(self):
        assert flag_cancelada("", prima_acumulada=5000) == 1

    def test_sin_estatus_sin_prima(self):
        assert flag_cancelada("", prima_acumulada=0) == 0


# ══════════════════════════════════════════════════════════════════
# CJ: FLAG NUEVA FORMAL
# ══════════════════════════════════════════════════════════════════

class TestFlagNuevaFormal:
    def test_vida_cancelada_fpago(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "CANC/X F.PAGO", ramo_codigo=11) == 0

    def test_vida_cancelada_sustitucion(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "CANC/X SUSTITUCION", ramo_codigo=11) == 0

    def test_vida_normal(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "PAGADA TOTAL", ramo_codigo=11) == 1

    def test_gmm_cancelada(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "CANCELADA", ramo_codigo=34) == 0

    def test_gmm_sin_estatus_sin_prima(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "", prima_acumulada=0, ramo_codigo=34) == 0

    def test_gmm_sin_estatus_con_prima(self):
        anio = datetime.now().year
        assert flag_nueva_formal(anio, "", prima_acumulada=5000, ramo_codigo=34) == 1

    def test_anio_viejo(self):
        assert flag_nueva_formal(2020, "CANCELADA", ramo_codigo=34) == 1


# ══════════════════════════════════════════════════════════════════
# CU: PRIMA PROPORCIONAL
# ══════════════════════════════════════════════════════════════════

class TestPrimaProporcional:
    def test_normal(self):
        """Con una fecha de referencia fija, verifica el cálculo."""
        r = prima_proporcional("2025-01-01", 36500.0, fecha_ref="2025-07-01")
        # 181 días / 365 * 36500 = 18,100
        assert r == pytest.approx(18100.0, abs=200)

    def test_sin_fecha(self):
        assert prima_proporcional("", 10000) == 0.0
        assert prima_proporcional(None, 10000) == 0.0

    def test_sin_prima(self):
        assert prima_proporcional("2025-01-01", 0) == 0.0

    def test_fecha_futura(self):
        """Si la póliza inicia en el futuro, debe ser 0."""
        futuro = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        assert prima_proporcional(futuro, 10000) == 0.0


# ══════════════════════════════════════════════════════════════════
# CV: CONDICIONAL PRIMA
# ══════════════════════════════════════════════════════════════════

class TestCondicionalPrima:
    def test_ok(self):
        assert condicional_prima(10000, 5000) == "OK"

    def test_cancelada(self):
        assert condicional_prima(3000, 5000) == "Cancelada"

    def test_iguales(self):
        assert condicional_prima(5000, 5000) == "OK"

    def test_nones(self):
        assert condicional_prima(None, None) == ""


# ══════════════════════════════════════════════════════════════════
# ORQUESTADOR: aplicar_reglas_poliza
# ══════════════════════════════════════════════════════════════════

class TestAplicarReglasPoliza:
    """Verifica que el orquestador calcula todos los campos esperados."""

    @pytest.fixture
    def poliza_vida(self):
        return {
            "poliza_original": "17958V00",
            "fecha_inicio": "2025-03-15",
            "prima_neta": 25000.0,
            "moneda": "MN",
            "mystatus": "PAGADA TOTAL",
            "status_recibo": "PAGADA",
            "anio_aplicacion": 2025,
            "fecha_aplicacion": "2025-04-01",
            "es_nueva": True,
        }

    @pytest.fixture
    def poliza_gmm_cancelada(self):
        return {
            "poliza_original": "18104U00",
            "fecha_inicio": "2025-01-01",
            "prima_neta": 12000.0,
            "moneda": "MN",
            "mystatus": "CANCELADA CADUCADA",
            "status_recibo": "CANCELADA",
            "anio_aplicacion": 2025,
            "fecha_aplicacion": "",
            "es_nueva": False,
        }

    def test_campos_retornados(self, poliza_vida):
        r = aplicar_reglas_poliza(poliza_vida, ramo_codigo=11)
        campos_esperados = {
            "largo_poliza", "raiz_poliza_6", "terminacion", "id_compuesto",
            "es_reexpedicion", "primer_anio", "fecha_aplicacion", "mes_aplicacion",
            "pendientes_pago", "trimestre", "flag_pagada", "flag_nueva_formal",
            "prima_anual_pesos", "prima_acumulada_basica", "equivalencias_emitidas",
            "equivalencias_pagadas", "flag_cancelada", "prima_proporcional",
            "condicional_prima",
        }
        assert campos_esperados.issubset(set(r.keys())), \
            f"Faltan campos: {campos_esperados - set(r.keys())}"

    def test_vida_values(self, poliza_vida):
        r = aplicar_reglas_poliza(poliza_vida, ramo_codigo=11)
        assert r["largo_poliza"] == 8
        assert r["raiz_poliza_6"] == "17958V"
        assert r["terminacion"] == "00"
        assert r["es_reexpedicion"] is False
        assert "2025" in r["primer_anio"]
        assert r["flag_pagada"] == 1
        assert r["prima_anual_pesos"] == 25000.0
        assert r["flag_cancelada"] == 1
        assert r["mes_aplicacion"] == "ABRIL"
        assert r["trimestre"] == "Q2"

    def test_cancelada_values(self, poliza_gmm_cancelada):
        r = aplicar_reglas_poliza(poliza_gmm_cancelada, ramo_codigo=34)
        assert r["flag_cancelada"] == 0
        assert r["flag_pagada"] == 0
        assert r["equivalencias_pagadas"] == 0.0


# ══════════════════════════════════════════════════════════════════
# BATCH: aplicar_reglas_batch
# ══════════════════════════════════════════════════════════════════

class TestAplicarReglasBatch:
    def test_reexpediciones_contadas(self):
        """Dos pólizas con la misma raíz → num_reexpediciones = 2."""
        polizas = [
            {
                "poliza_original": "17958V00",
                "fecha_inicio": "2025-03-15",
                "prima_neta": 25000.0, "moneda": "MN",
                "mystatus": "PAGADA TOTAL", "status_recibo": "PAGADA",
                "anio_aplicacion": 2025, "fecha_aplicacion": "2025-04-01",
                "ramo_nombre": "VIDA",
            },
            {
                "poliza_original": "17958V01",
                "fecha_inicio": "2025-06-01",
                "prima_neta": 25000.0, "moneda": "MN",
                "mystatus": "PAGADA TOTAL", "status_recibo": "PAGADA",
                "anio_aplicacion": 2025, "fecha_aplicacion": "2025-07-01",
                "ramo_nombre": "VIDA",
            },
        ]
        results = aplicar_reglas_batch(polizas)
        assert len(results) == 2
        # Both share raiz "17958V" → count = 2
        assert results[0]["num_reexpediciones"] == 2
        assert results[1]["num_reexpediciones"] == 2

    def test_lote_mixto_ramo(self):
        """Si no se pasa ramo_codigo, lo infiere del ramo_nombre."""
        polizas = [
            {
                "poliza_original": "17958V00",
                "fecha_inicio": "2025-03-15",
                "prima_neta": 25000.0, "moneda": "MN",
                "mystatus": "", "status_recibo": "PAGADA",
                "anio_aplicacion": 2025, "fecha_aplicacion": "2025-04-01",
                "ramo_nombre": "VIDA INDIVIDUAL",
            },
            {
                "poliza_original": "18200U00",
                "fecha_inicio": "2025-02-01",
                "prima_neta": 15000.0, "moneda": "MN",
                "mystatus": "", "status_recibo": "PAGADA",
                "anio_aplicacion": 2025, "fecha_aplicacion": "2025-03-01",
                "ramo_nombre": "GASTOS MEDICOS",
            },
        ]
        results = aplicar_reglas_batch(polizas)
        assert len(results) == 2
        assert all("largo_poliza" in r for r in results)
        assert all("num_reexpediciones" in r for r in results)


# ══════════════════════════════════════════════════════════════════
# Constantes y catálogos
# ══════════════════════════════════════════════════════════════════

class TestConstantes:
    def test_catalogo_estatus_tiene_6(self):
        assert len(CATALOGO_ESTATUS) == 6

    def test_estatus_cubo_map_completo(self):
        assert len(ESTATUS_CUBO_MAP) == 7  # 7 entradas mapeadas

    def test_segmentos_tiene_8(self):
        assert len(SEGMENTOS) == 8

    def test_estatus_cancelada_set(self):
        assert "CANC/X F.PAGO" in ESTATUS_CANCELADA
        assert "CANCELADA" in ESTATUS_CANCELADA


# ══════════════════════════════════════════════════════════════════
# KPIs Dashboard
# ══════════════════════════════════════════════════════════════════

class TestCalcularKPIs:
    def test_kpis_basicos(self):
        polizas = [
            {"anio_aplicacion": 2025, "ramo_codigo": 11, "tipo_poliza": "NUEVA",
             "tipo_prima": "BASICA", "prima_neta": 20000, "mystatus": "PAGADA"},
            {"anio_aplicacion": 2025, "ramo_codigo": 34, "tipo_poliza": "NUEVA",
             "tipo_prima": None, "prima_neta": 15000, "num_asegurados": 3, "mystatus": ""},
            {"anio_aplicacion": 2025, "ramo_codigo": 34, "tipo_poliza": "SUBSECUENTE",
             "tipo_prima": None, "prima_neta": 8000, "mystatus": "CANCELADA"},
        ]
        r = calcular_kpis_polizas(polizas, 2025)
        assert r["polizas_nuevas_vida"] == 1
        assert r["prima_nueva_vida"] == 20000
        assert r["polizas_nuevas_gmm"] == 1
        assert r["asegurados_nuevos_gmm"] == 3
        assert r["prima_nueva_gmm"] == 15000
        assert r["prima_subsecuente_gmm"] == 8000
        assert r["canceladas_gmm"] == 1
        assert r["total_polizas"] == 3

    def test_kpis_sin_datos(self):
        r = calcular_kpis_polizas([], 2025)
        assert r["total_polizas"] == 0
        assert r["polizas_nuevas_vida"] == 0


# ══════════════════════════════════════════════════════════════════
# BV: Pendientes de pago (edge cases)
# ══════════════════════════════════════════════════════════════════

class TestDetectarPendientesPago:
    def test_sin_fecha(self):
        assert detectar_pendientes_pago("", "", "-", False) == ""

    def test_fecha_antigua(self):
        """Inicio más de 30 días atrás → vacío."""
        antigua = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        assert detectar_pendientes_pago(antigua, "", "-", False) == ""


# ══════════════════════════════════════════════════════════════════
# Fase 3: Cadena de renovaciones
# ══════════════════════════════════════════════════════════════════

class TestCadenaRenovaciones:
    def test_cadena_simple(self):
        polizas = [
            {"id": 1, "poliza": "17958V00", "raiz": "17958V", "version": 0, "anio": 2023},
            {"id": 2, "poliza": "17958V01", "raiz": "17958V", "version": 1, "anio": 2024},
            {"id": 3, "poliza": "17958V02", "raiz": "17958V", "version": 2, "anio": 2025},
        ]
        cadena = construir_cadena_renovaciones(polizas)
        assert cadena[2] == 1  # V01 apunta a V00
        assert cadena[3] == 2  # V02 apunta a V01
        assert 1 not in cadena  # V00 es la madre, no apunta a nadie

    def test_sin_renovaciones(self):
        polizas = [
            {"id": 1, "poliza": "17958V00", "raiz": "17958V", "version": 0, "anio": 2023},
            {"id": 2, "poliza": "99999U00", "raiz": "99999U", "version": 0, "anio": 2024},
        ]
        cadena = construir_cadena_renovaciones(polizas)
        assert len(cadena) == 0  # No hay renovaciones

    def test_multiples_cadenas(self):
        polizas = [
            {"id": 1, "poliza": "17958V00", "raiz": "17958V", "version": 0, "anio": 2023},
            {"id": 2, "poliza": "17958V01", "raiz": "17958V", "version": 1, "anio": 2024},
            {"id": 3, "poliza": "99999U00", "raiz": "99999U", "version": 0, "anio": 2023},
            {"id": 4, "poliza": "99999U01", "raiz": "99999U", "version": 1, "anio": 2025},
        ]
        cadena = construir_cadena_renovaciones(polizas)
        assert cadena[2] == 1
        assert cadena[4] == 3


# ══════════════════════════════════════════════════════════════════
# Fase 3: Cálculo de faltantes
# ══════════════════════════════════════════════════════════════════

class TestCalcularFaltantes:
    def test_faltante_normal(self):
        r = calcular_faltantes(meta_polizas=10, meta_prima=100000, real_polizas=6, real_prima=60000)
        assert r["faltante_polizas"] == 4
        assert r["faltante_prima"] == 40000
        assert r["pct_cumplimiento"] == 60.0

    def test_superado(self):
        r = calcular_faltantes(meta_polizas=10, meta_prima=100000, real_polizas=12, real_prima=120000)
        assert r["faltante_polizas"] == 0
        assert r["faltante_prima"] == 0
        assert r["pct_cumplimiento"] == 120.0

    def test_ceros(self):
        r = calcular_faltantes()
        assert r["faltante_polizas"] == 0
        assert r["pct_cumplimiento"] == 0


# ══════════════════════════════════════════════════════════════════
# Fase 3: Mystatus temporal enriquecido
# ══════════════════════════════════════════════════════════════════

class TestMystatusEnriquecido:
    def test_modificacion_poliza(self):
        assert calcular_mystatus("", "POLIZA CANCELADA", "REDUCCION DE PRIMA") == "CANCELADA POR MODIFICACION"
        assert calcular_mystatus("", "POLIZA CANCELADA", "AUMENTO DE PRIMA") == "CANCELADA POR MODIFICACION"

    def test_fallback_canc_no_tomada(self):
        assert calcular_mystatus("CANC/NO TOMADA") == "CANCELADA NO TOMADA"

    def test_fallback_pendiente(self):
        assert calcular_mystatus("PENDIENTE") == "PENDIENTE DE PAGO"

    def test_fallback_rehabilitada(self):
        assert calcular_mystatus("REHABILITADA") == "REHABILITADA"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
