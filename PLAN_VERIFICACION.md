# ✅ Plan de Verificación — Motor de Reglas MAG-AXA

**Fecha:** 25 de febrero de 2026  
**Versión:** v0.2.0 — Columnas AUTOMATICO (BG–CW) integradas  
**Resultado actual:** 🟢 145 tests passed (0.16s)

---

## 📋 Resumen de Cobertura

| Módulo | Funciones | Tests | Estado |
|--------|-----------|-------|--------|
| **R1+R2** Clasificación Nueva/Subsecuente | `clasificar_poliza` | 9 | ✅ |
| **R3** Asegurado nuevo GMM | `es_asegurado_nuevo_gmm` | 4 | ✅ |
| **R4** Frontera de año | `alerta_frontera_anio` | 7 | ✅ |
| **R5** Reexpediciones | `es_reexpedicion`, `extraer_raiz_poliza` | 5 | ✅ |
| **R6** MYSTATUS | `calcular_mystatus` | 9 | ✅ |
| **R7** Normalización | `normalizar_poliza` | 5 | ✅ |
| Segmentos | `agrupar_segmento` | 11 | ✅ |
| Estatus Cubo | `mapear_estatus_cubo` | 9 | ✅ |
| Clasificación CY | `clasificar_cy` | 3 | ✅ |
| **BG** Largo póliza | `largo_poliza` | 3 | ✅ |
| **BH** Raíz póliza 6 | `raiz_poliza_6` | 3 | ✅ |
| **BI** Terminación | `terminacion_poliza` | 4 | ✅ |
| **BT** ID compuesto | `generar_id_compuesto` | 2 | ✅ |
| **BJ** Primer año | `determinar_primer_anio` | 5 | ✅ |
| **BL** Mes aplicación | `mes_aplicacion` | 5 | ✅ |
| **BV** Pendientes pago | `detectar_pendientes_pago` | 2 | ✅ |
| **CA** Trimestre | `calcular_trimestre` | 11 | ✅ |
| **CI** Flag pagada | `flag_pagada` | 3 | ✅ |
| **CJ** Nueva formal | `flag_nueva_formal` | 7 | ✅ |
| **CM** Prima en pesos | `prima_anual_en_pesos` | 5 | ✅ |
| **CN** Equivalencias | `calcular_equivalencias` | 5 | ✅ |
| **CO** Equiv pagadas | `calcular_equivalencias_pagadas` | 4 | ✅ |
| **CP** Flag cancelada | `flag_cancelada` | 4 | ✅ |
| **CU** Prima proporcional | `prima_proporcional` | 4 | ✅ |
| **CV** Condicional prima | `condicional_prima` | 4 | ✅ |
| KPIs Dashboard | `calcular_kpis_polizas` | 2 | ✅ |
| Orquestador | `aplicar_reglas_poliza` | 3 | ✅ |
| Batch | `aplicar_reglas_batch` | 2 | ✅ |
| Constantes | catálogos y sets | 4 | ✅ |
| **TOTAL** | **25+ funciones** | **145 tests** | **🟢** |

---

## 🔬 Verificación Automatizada

### Ejecutar todos los tests

```powershell
cd C:\Users\jlcue\Documents\mag-sistema
python -m pytest tests/test_rules.py -v --tb=short
```

### Ejecutar un grupo específico

```powershell
# Solo las reglas originales (R1-R7)
python -m pytest tests/test_rules.py -k "TestClasificarPoliza or TestReexpedicion or TestCalcularMystatus" -v

# Solo las columnas AUTOMATICO (BG-CW) 
python -m pytest tests/test_rules.py -k "TestLargo or TestRaiz or TestTerminacion or TestEquivalencias or TestPrima" -v

# Solo el orquestador
python -m pytest tests/test_rules.py -k "TestAplicarReglas" -v
```

---

## 🔍 Verificación Manual — Checklist

### 1. API en funcionamiento

```powershell
cd C:\Users\jlcue\Documents\mag-sistema
python -m uvicorn main:app --host 127.0.0.1 --port 8000
# Abrir: http://127.0.0.1:8000/docs
```

- [ ] `GET /` → responde con info del sistema
- [ ] `GET /health` → `{"status": "ok"}`
- [ ] `GET /dashboard?anio=2025` → retorna KPIs
- [ ] `GET /polizas?page=1&limit=10` → lista pólizas con campos calculados
- [ ] `POST /importar/aplicar-reglas?anio=2025` → recalcula todos los campos AUTOMATICO

### 2. Endpoint `/importar/aplicar-reglas`

- [ ] Verificar que recalcula `largo_poliza`, `raiz_poliza_6`, `terminacion`
- [ ] Verificar que `equivalencias_emitidas` y `equivalencias_pagadas` se calculan correctamente
- [ ] Verificar que `prima_anual_pesos` convierte USD y UDIS a MXN
- [ ] Verificar que `flag_cancelada` es 0 para pólizas con estatus cancelado
- [ ] Verificar que `condicional_prima` marca "Cancelada" cuando prima acumulada < prima proporcional

### 3. Cruce con datos del Excel AUTOMATICO

Para validar que las fórmulas Python coinciden con el Excel original:

| Columna Excel | Función Python | Verificar con póliza ejemplo |
|---------------|---------------|------------------------------|
| BG: `=LEN(AD2)` | `largo_poliza()` | Póliza `17958V00` → 8 |
| BH: `=LEFT(AD2,6)` | `raiz_poliza_6()` | `17958V00` → `17958V` |
| BI: `=RIGHT(AD2,2)` | `terminacion_poliza()` | `17958V00` → `00` |
| BT: `=AD2&T2` | `generar_id_compuesto()` | `17958V00` + `2025-01-15` → `17958V002025-01-15` |
| BL: `=UPPER(TEXT(BK2,"MMMM"))` | `mes_aplicacion()` | `2025-01-15` → `ENERO` |
| CM: moneda × TC | `prima_anual_en_pesos()` | 1000 UDIS → $8,560.00 |
| CN: rangos de prima | `calcular_equivalencias()` | $30,000 MN → 1.0 equiv |

---

## 📊 Mapeo Excel → Python Completo

| Col Excel | Nombre Campo | Referencia Excel | Función Python | Columna BD |
|-----------|-------------|-----------------|----------------|------------|
| BG | Largo | `=LEN(AD2)` | `largo_poliza()` | `largo_poliza` |
| BH | Raíz 6 | `=LEFT(AD2,6)` | `raiz_poliza_6()` | `raiz_poliza_6` |
| BI | Terminación | `=RIGHT(AD2,2)` | `terminacion_poliza()` | `terminacion` |
| BF | Reexpediciones | `=COUNTIF($BH:$BH,BH2)` | batch en `aplicar_reglas_batch()` | `num_reexpediciones` |
| BJ | Primer Año | IF anidados | `determinar_primer_anio()` | `primer_anio` |
| BT | ID Compuesto | `=AD2&T2` | `generar_id_compuesto()` | `id_compuesto` |
| BU/BK | Fec Apli | condicional | inferida en `aplicar_reglas_poliza()` | `fecha_aplicacion` |
| BL | Mes Apli | `=UPPER(TEXT(...))` | `mes_aplicacion()` | `mes_aplicacion` |
| BV | Pendientes | IF anidados | `detectar_pendientes_pago()` | `pendientes_pago` |
| CA | Trimestre | IF mes ranges | `calcular_trimestre()` | `trimestre` |
| CF | Prima Acum | `=SUMIFS(...)` | se recibe como dato | `prima_acumulada_basica` |
| CI | Pagada | `=IF(BU2="-",0,1)` | `flag_pagada()` | `flag_pagada` |
| CJ | Nueva Formal | IF estatus | `flag_nueva_formal()` | `flag_nueva_formal` |
| CM | Prima Pesos | IF moneda×TC | `prima_anual_en_pesos()` | `prima_anual_pesos` |
| CN | Equiv Emit | IF rangos prima | `calcular_equivalencias()` | `equivalencias_emitidas` |
| CO | Equiv Pag | IF cancel+CI+rangos | `calcular_equivalencias_pagadas()` | `equivalencias_pagadas` |
| CP | Cancelada | IF OR estatus | `flag_cancelada()` | `flag_cancelada` |
| CU | Prima Prop | `=(ref-T2)/365*CM2` | `prima_proporcional()` | `prima_proporcional` |
| CV | Cond Prima | `=IF(CF2<CU2,...)` | `condicional_prima()` | `condicional_prima` |

---

## ⚠️ Notas Importantes

1. **Tipos de cambio:** Los TC de UDIS ($8.56) y USD ($18.38) son valores hardcoded del Excel original. Se pueden configurar via variables de entorno `MAG_TC_UDIS` y `MAG_TC_USD`.

2. **Prima proporcional:** Usa `TODAY()-28` como fecha de referencia por defecto (igual que el Excel). Para tests deterministas se usa `fecha_ref` explícita.

3. **Pendientes de pago:** La lógica usa `datetime.now()` para la ventana de 30 días. En producción esto es correcto; en tests se verifica con fechas futuras y pasadas.

4. **El batch processor** (`aplicar_reglas_batch`) es necesario para `num_reexpediciones` ya que es un COUNTIF sobre el conjunto completo.

---

*Plan generado automáticamente el 25 de febrero de 2026*
