# Drilldown Completo: Campos de Póliza
## MAG Sistema — Modelo de Datos `Poliza`

> **80+ campos** divididos en 7 categorías: Identidad, Asegurado, Fechas, Primas, Clasificación, Cubo AXA, y Campos Calculados (Motor de Reglas).

---

## 📋 Resumen Rápido

| Categoría | Campos | Origen |
|---|---|---|
| 🔑 Identidad & Estructura | 7 | Importado |
| 👤 Asegurado / Contratante | 7 | Importado |
| 📅 Fechas | 5 | Importado |
| 💰 Primas & Financieros | 15 | Importado |
| 📊 Producto & Cobertura | 10 | Importado |
| 📦 Cubo AXA (Reporte) | 13 | Importado |
| 🧮 Calculados (Motor Reglas) | 20 | Calculado por `rules.py` |
| 🔗 Relaciones & Sistema | 7 | Sistema |
| **Total** | **~84** | |

---

## 🔑 1. IDENTIDAD & ESTRUCTURA
> Campos que identifican la póliza y su estructura de versiones.

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 1 | `id` | Integer PK | No | — | ID auto-generado |
| 2 | `poliza_original` | String(30) | No | Col AD: `POLIZA` | Número de póliza tal cual viene del Excel |
| 3 | `poliza_estandar` | String(30) | No | — | Póliza normalizada (sin ceros iniciales) via `normalizar_poliza()` |
| 4 | `version` | Integer | Sí | — | Versión de reexpedición (0 = original, 1+ = reexpedida) |
| 5 | `solicitud` | String(30) | Sí | Col E: `SOLICITUD` | Número de solicitud AXA |
| 6 | `archivo_pdf` | String(200) | Sí | — | Ruta al PDF de la póliza (futuro) |
| 7 | `poliza_padre_id` | Integer FK | Sí | — | ID de la póliza madre (cadena de renovaciones, Regla 8) |

---

## 👤 2. ASEGURADO / CONTRATANTE
> Datos del titular y contacto.

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 8 | `asegurado_nombre` | String(200) | Sí | Col F: `ASEGURADO` | Nombre completo del asegurado |
| 9 | `contratante_nombre` | String(200) | Sí | Col G: `CONTRATANTE` | Nombre del contratante (puede diferir del asegurado) |
| 10 | `rfc` | String(20) | Sí | — | RFC del contratante |
| 11 | `codigo_postal` | String(10) | Sí | — | Código postal |
| 12 | `telefono` | String(20) | Sí | — | Teléfono de contacto |
| 13 | `email` | String(200) | Sí | — | Email de contacto |
| 14 | `num_asegurados` | Integer | Sí | Col H o calculado | Número de asegurados (GMM: puede ser >1) |

---

## 📅 3. FECHAS
> Temporalidad del contrato de seguro.

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 15 | `fecha_emision` | String(10) | Sí | Col S: `FEC EMISION` | Fecha de emisión de la póliza `YYYY-MM-DD` |
| 16 | `fecha_inicio` | String(10) | **No** | Col T: `FEC INICIO VIG` | Fecha de inicio de vigencia — campo clave para muchos cálculos |
| 17 | `fecha_fin` | String(10) | Sí | Col U: `FEC FIN VIG` | Fecha de fin de vigencia |
| 18 | `fecha_primer_pago` | String(10) | Sí | Cubo | Fecha del primer pago recibido |
| 19 | `fecha_ultimo_pago` | String(10) | Sí | Cubo | Fecha del último pago recibido |

---

## 💰 4. PRIMAS & FINANCIEROS
> Todos los valores económicos de la póliza.

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 20 | `moneda` | String(5) | Sí | Col Y: `MONEDA` | `MN` (pesos), `UDIS`, `USD` |
| 21 | `prima_total` | Float | Sí | Col AE | Prima total del recibo (con IVA + recargos) |
| 22 | `prima_neta` | Float | Sí | Col AF: `PRIMA NETA` | **Campo principal.** Prima neta sin IVA ni recargos |
| 23 | `iva` | Float | Sí | — | IVA aplicado |
| 24 | `recargo` | Float | Sí | — | Recargo por fraccionamiento |
| 25 | `derecho_poliza` | Float | Sí | — | Derecho de póliza |
| 26 | `suma_asegurada` | Float | Sí | Col AG: `SUMA ASEG` | Suma asegurada contratada |
| 27 | `deducible` | Float | Sí | — | Monto de deducible (GMM) |
| 28 | `coaseguro` | Float | Sí | — | Porcentaje de coaseguro (GMM) |
| 29 | `tope` | Float | Sí | — | Tope de coaseguro (GMM) |
| 30 | `pct_comision` | Float | Sí | Calculado R2 | Porcentaje de comisión (para clasificación BASICA/EXCEDENTE) |
| 31 | `neta_total_contrato` | Float | Sí | Cubo | Prima neta total del contrato completo |
| 32 | `neta_acumulada` | Float | Sí | Cubo | Prima neta acumulada de pagos recibidos |
| 33 | `neta_forma_pago` | Float | Sí | Cubo | Prima ajustada por forma de pago |
| 34 | `neta_sin_forma` | Float | Sí | Cubo | Prima sin ajuste de forma de pago |
| 35 | `neta_cancelacion` | Float | Sí | Cubo | Prima con impacto de cancelación |

---

## 📊 5. PRODUCTO & COBERTURA
> Características del plan de seguro.

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 36 | `agente_id` | Integer FK | Sí | Lookup | FK a tabla `agentes` (resuelto por `codigo_agente`) |
| 37 | `producto_id` | Integer FK | Sí | Lookup | FK a tabla `productos` (resuelto por ramo+plan+gama) |
| 38 | `forma_pago` | String(20) | Sí | Col Z: `FORMA PAGO` | `ANUAL`, `SEMESTRAL`, `TRIMESTRAL`, `MENSUAL` |
| 39 | `tipo_pago` | String(30) | Sí | Col AA | Tipo de pago: `CARGO AUTOMATICO`, `REFERENCIADO`, etc. |
| 40 | `status_recibo` | String(50) | Sí | Col AM: `STATUS RECIBO` | Estatus AXA original: `PAGADA`, `CANCELADA FP`, `NO TOMADA`, etc. |
| 41 | `plazo_pago` | String(30) | Sí | — | Plazo de pago |
| 42 | `zona` | String(20) | Sí | — | Zona geográfica (GMM) |
| 43 | `red` | String(30) | Sí | — | Red médica (GMM): `NACIONAL`, `INTERNACIONAL` |
| 44 | `tabulador` | String(30) | Sí | — | Tabulador de precios (GMM) |
| 45 | `maternidad` | String(20) | Sí | — | Cobertura de maternidad (GMM) |
| 46 | `cobertura` | Text | Sí | — | Descripción de coberturas |
| 47 | `gama` | String(50) | Sí | Col AB | Gama de producto (GMM): `PREMIER`, `GOLD`, `CLASSIC`, etc. |

---

## 📦 6. CUBO AXA (Campos del Reporte Cubo 2025)
> Campos importados directamente del Reporte de Cubo AXA (hojas RESUMEN/DETALLE).

| # | Campo DB | Tipo | Nullable | Origen Excel | Descripción |
|---|---|---|---|---|---|
| 48 | `segmento` | String(50) | Sí | Cubo: `SEGMENTO` | Segmento comercial: `ALFA TOP INTEGRAL`, `BETA1`, `OMEGA`, etc. |
| 49 | `gestion_comercial` | String(100) | Sí | Cubo | Gestión comercial: `ALFA/MARIA ESTHER`, `BETA/EDGAR` |
| 50 | `lider_codigo` | String(20) | Sí | Cubo | Código del agente líder de la gestión |
| 51 | `clasificacion_cy` | String(30) | Sí | Cubo: `CLASIF CY` | Clasificación current year: `CY SUBSECUENTE`, `CY ANUAL` |
| 52 | `estatus_cubo` | String(50) | Sí | Cubo: `ESTATUS` | Estatus según el Cubo: `POLIZA PAGADA`, `POLIZA AL CORRIENTE`, `POLIZA CANCELADA`, etc. |
| 53 | `estatus_detalle` | String(100) | Sí | Cubo: detalle | Detalle del estatus: `FALTA DE PAGO`, `NO TOMADA`, `A PETICION`, etc. |
| 54 | `nueva_poliza_flag` | Integer | Sí | Cubo | 1 si AXA la marca como nueva, 0 si no |
| 55 | `anio_conf` | Integer | Sí | Cubo | Año de confirmación del período |
| 56 | `mes_conf` | Integer | Sí | Cubo | Mes de confirmación del período |
| 57 | `es_nueva` | Boolean | Sí | R1 / Cubo | Si la póliza es nueva (combinación de reglas + flag cubo) |
| 58 | `tipo_poliza` | String(20) | Sí | R1: `clasificar_poliza()` | `NUEVA`, `SUBSECUENTE`, `NO_APLICA` |
| 59 | `tipo_prima` | String(20) | Sí | R2 | `BASICA` o `EXCEDENTE` (solo Vida, por umbral 2.1%) |
| 60 | `es_reexpedicion` | Boolean | Sí | R5: `es_reexpedicion()` | `True` si terminación ≠ `00` |

---

## 🧮 7. CAMPOS CALCULADOS (Motor de Reglas `rules.py`)
> Generados automáticamente por el motor de reglas. Equivalen a las columnas BG–CW del AUTOMATICO Excel.

### 7.1 Derivados de la estructura de póliza

| # | Campo DB | Col Excel | Función `rules.py` | Descripción | Ejemplo |
|---|---|---|---|---|---|
| 61 | `largo_poliza` | BG | `largo_poliza()` | `LEN(poliza)` — longitud del número | `10` |
| 62 | `raiz_poliza_6` | BH | `raiz_poliza_6()` | `LEFT(poliza,6)` — primeros 6 chars | `"007638"` |
| 63 | `terminacion` | BI | `terminacion_poliza()` | `RIGHT(poliza,2)` — últimos 2 chars | `"00"`, `"01"` |
| 64 | `num_reexpediciones` | BF | `aplicar_reglas_batch()` | `COUNTIF` de pólizas con misma raíz | `3` |
| 65 | `id_compuesto` | BT | `generar_id_compuesto()` | `poliza + fecha_inicio` — ID único | `"0076384A2025-01-15"` |

### 7.2 Temporalidad y períodos

| # | Campo DB | Col Excel | Función `rules.py` | Descripción | Ejemplo |
|---|---|---|---|---|---|
| 66 | `primer_anio` | BJ | `determinar_primer_anio()` | Clasificación de primer año con lógica multi-fuente | `"PRIMER AÑO 2025"`, `"-"` |
| 67 | `fecha_aplicacion` | BU/BK | `aplicar_reglas_poliza()` | Fecha de aplicación (pagos vs emisión) | `"2025-03-15"` |
| 68 | `mes_aplicacion` | BL | `mes_aplicacion()` | Nombre del mes en español (mayúsculas) | `"MARZO"` |
| 69 | `trimestre` | CA | `calcular_trimestre()` | Trimestre fiscal | `"Q1"`, `"Q2"`, `"Q3"`, `"Q4"` |
| 70 | `periodo_aplicacion` | — | Derivado | Período `YYYY-MM` | `"2025-03"` |
| 71 | `anio_aplicacion` | — | Derivado | Año numérico | `2025` |

### 7.3 Flags de estado (0/1)

| # | Campo DB | Col Excel | Función `rules.py` | Lógica | Valores |
|---|---|---|---|---|---|
| 72 | `flag_pagada` | CI | `flag_pagada()` | `1` si tiene fecha_aplicacion, `0` si no | `0` / `1` |
| 73 | `flag_nueva_formal` | CJ | `flag_nueva_formal()` | `1` si es nueva formalmente (excluye CANC/X F.PAGO, CANC/X SUSTITUCION) | `0` / `1` |
| 74 | `flag_cancelada` | CP | `flag_cancelada()` | `0` si cancelada (NO TOMADA, F.PAGO, etc.), `1` si vigente | `0` / `1` |

### 7.4 Primas calculadas y equivalencias

| # | Campo DB | Col Excel | Función `rules.py` | Descripción | Ejemplo |
|---|---|---|---|---|---|
| 75 | `prima_acumulada_basica` | CF | `aplicar_reglas_poliza()` | Prima acumulada pagada (viene de `neta_acumulada`) | `35000.0` |
| 76 | `prima_anual_pesos` | CM | `prima_anual_en_pesos()` | Prima convertida a MXN (`UDIS×8.56`, `USD×18.38`) | `42000.0` |
| 77 | `equivalencias_emitidas` | CN | `calcular_equivalencias()` | Pólizas equivalentes emitidas por rango de prima | `0.5`, `1.0`, `2.0` |
| 78 | `equivalencias_pagadas` | CO | `calcular_equivalencias_pagadas()` | Equiv. pagadas (solo si no cancelada y tiene pago) | `0.5`, `1.0`, `2.0` |
| 79 | `prima_proporcional` | CU | `prima_proporcional()` | Prima proporcional al tiempo transcurrido (días/365 × prima) | `28500.0` |

### 7.5 Alertas y validaciones

| # | Campo DB | Col Excel | Función `rules.py` | Descripción | Ejemplo |
|---|---|---|---|---|---|
| 80 | `pendientes_pago` | BV | `detectar_pendientes_pago()` | Etiqueta si tiene pago pendiente | `"PRIMER AÑO 2025 PENDIENTE PAGO"`, `""` |
| 81 | `condicional_prima` | CV/CN | `condicional_prima()` | `"OK"` si acumulada ≥ proporcional, `"Cancelada"` si no | `"OK"`, `"Cancelada"` |
| 82 | `mystatus` | BD | `calcular_mystatus()` | Motor de 6 estatus enriquecido (ver abajo) | `"PAGADA"`, `"ATRASADA"` |

---

## 🔗 8. RELACIONES & SISTEMA

| # | Campo DB | Tipo | Descripción |
|---|---|---|---|
| 83 | `contratante_id` | Integer FK | FK a tabla `contratantes` (Fase 5.1) |
| 84 | `fuente` | String(50) | Origen del registro: `EXCEL_IMPORT`, `MANUAL`, `API` |
| 85 | `notas` | Text | Notas libres |
| 86 | `created_at` | String(30) | Timestamp de creación |
| 87 | `updated_at` | String(30) | Timestamp de última modificación |

**Relaciones ORM:**
- `agente` → `Agente` (via `agente_id`)
- `producto` → `Producto` (via `producto_id`)
- `recibos` → `[Recibo]` (one-to-many)
- `contratante_rel` → `Contratante` (via `contratante_id`)

---

## 🧠 Motor de Reglas — Detalle de Funciones

### Regla 1+2: `clasificar_poliza()`
```
IF ramo=11 (Vida):
  IF fecha_inicio.year == anio_analisis AND status ∈ {PAGADA, AL CORRIENTE, PENDIENTE}:
    IF comision/prima >= 0.021 → NUEVA + BASICA
    ELSE → NUEVA + EXCEDENTE
  ELSE → SUBSECUENTE
IF ramo=34 (GMM):
  IF fecha_inicio.year == anio_analisis AND status ∈ {PAGADA, AL CORRIENTE} → NUEVA
  ELSE → SUBSECUENTE
```

### Regla 5: `es_reexpedicion()`
```
Terminación "00" → Original
Terminación ≠ "00" → Reexpedida (ej: "01", "02", "A1")
```

### Regla 6: `calcular_mystatus()` — Motor de 6 Estatus
```
Catálogo:
  1. PENDIENTE DE PAGO — Emitida < 30 días, sin pago
  2. PAGADA — Prima pagada = prima neta (tolerancia 5%)
  3. AL CORRIENTE — Prima pagada > 0 pero < neta
  4. ATRASADA — Emitida > 30 días, sin pago completo
  5. CANCELADA — Estatus AXA contiene "CANC" o "NO TOMADA"
  6. REHABILITADA — Estatus cubo = "POLIZA REHABILITADA"
```

### Equivalencias (CN/CO):
```
Rangos 2025:
  Prima < $16,000  → 0.5 equiv
  $16,000 ≤ Prima < $50,000 → 1.0 equiv
  Prima ≥ $50,000 → 2.0 equiv
  
Rangos 2024:
  Prima < $15,000  → 0.5 equiv
  $15,000 ≤ Prima < $50,000 → 1.0 equiv
  Prima ≥ $50,000 → 2.0 equiv
```

### Conversión de Moneda (CM):
```
MN → sin cambio
UDIS → prima × 8.56
USD → prima × 18.38
```

---

## 📌 Mapeo Excel → DB (Columnas Principales)

| Columna Excel | Campo DB | Categoría |
|---|---|---|
| AD: POLIZA | `poliza_original` | Identidad |
| E: SOLICITUD | `solicitud` | Identidad |
| F: ASEGURADO | `asegurado_nombre` | Asegurado |
| G: CONTRATANTE | `contratante_nombre` | Asegurado |
| S: FEC EMISION | `fecha_emision` | Fechas |
| T: FEC INICIO VIG | `fecha_inicio` | Fechas |
| U: FEC FIN VIG | `fecha_fin` | Fechas |
| Y: MONEDA | `moneda` | Primas |
| Z: FORMA PAGO | `forma_pago` | Producto |
| AE: PRIMA TOTAL | `prima_total` | Primas |
| AF: PRIMA NETA | `prima_neta` | Primas |
| AG: SUMA ASEG | `suma_asegurada` | Primas |
| AM: STATUS RECIBO | `status_recibo` | Producto |
| AB: GAMA | `gama` | Producto |
| BG | `largo_poliza` | Calculado |
| BH | `raiz_poliza_6` | Calculado |
| BI | `terminacion` | Calculado |
| BJ | `primer_anio` | Calculado |
| BK/BU | `fecha_aplicacion` | Calculado |
| BL | `mes_aplicacion` | Calculado |
| BT | `id_compuesto` | Calculado |
| BV | `pendientes_pago` | Calculado |
| CA | `trimestre` | Calculado |
| CF | `prima_acumulada_basica` | Calculado |
| CI | `flag_pagada` | Calculado |
| CJ | `flag_nueva_formal` | Calculado |
| CM | `prima_anual_pesos` | Calculado |
| CN | `equivalencias_emitidas` | Calculado |
| CO | `equivalencias_pagadas` | Calculado |
| CP | `flag_cancelada` | Calculado |
| CU | `prima_proporcional` | Calculado |
| CV/CN | `condicional_prima` | Calculado |

---

*Generado: 2026-02-26 | Versión: v0.2.0 | Fuente: `api/database.py` + `api/rules.py`*
