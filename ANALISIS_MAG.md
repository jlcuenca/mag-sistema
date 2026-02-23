# Análisis del Folder MAG – Promotoría de Seguros AXA

**Fecha de análisis:** 23 de febrero de 2026  
**Carpeta:** `d:\Documentos\GitHub\jl\mag`

---

## 📋 Resumen General

El folder `mag` contiene **6 archivos** relacionados con la operación de una **promotoría de seguros AXA** que maneja los ramos de **Vida Individual** y **Gastos Médicos Mayores (GMM) Individual**. Los archivos documentan:

1. Los procedimientos operativos para clasificar y validar pólizas/primas
2. Las bases de datos de pólizas y producción
3. Los indicadores de desempeño (KPIs) de AXA
4. La oferta de valor de la promotoría

---

## 📂 Inventario de Archivos

| # | Archivo | Tipo | Tamaño | Descripción |
|---|---------|------|--------|-------------|
| 1 | `Procedimiento_Polizas_Primas_AXA.docx` | Word | 30 KB | Procedimiento para clasificar pólizas nuevas vs. subsecuentes y sus primas |
| 2 | `Procedimiento_Revision_Indicadores_AXA.docx` | Word | 34 KB | Procedimiento para validar los indicadores oficiales de AXA |
| 3 | `POLIZAS01_19022026 (1).xlsx` | Excel | 3.4 MB | Base de pólizas al 19/feb/2026 con 3 hojas (querys, VIDA, GMM) |
| 4 | `Reporte 19 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO.xlsm` | Excel Macro | 103 MB | Base maestra con 57 hojas: conciliaciones, indicadores, resúmenes, producción, directorio de agentes |
| 5 | `original base de VIDA Y GMM_DIC (VF3DIC)HF (1).xlsx` | Excel | 173 MB | Base original histórica (diciembre) con 31 hojas: indicadores 2023-2025, deudor, datos fijos, directorio |
| 6 | `Oferta_valor_12_63931 (1).xlsb` | Excel Binario | 4.1 MB | Oferta de valor (formato binario .xlsb) |

---

## 1. Análisis de Procedimientos Operativos

### 1.1 Procedimiento de Clasificación de Pólizas y Primas

**Archivo:** `Procedimiento_Polizas_Primas_AXA.docx`

**Propósito:** Definir cómo clasificar las pólizas como **nuevas** o **subsecuentes** para el cálculo correcto de las métricas de producción ante AXA.

#### Flujo General:
```
Base Interna (POLIZAS01) → Clasificación (Nueva/Subsecuente) → Validación vs. Indicadores AXA → Reporte de Diferencias
```

#### Reglas de Clasificación:

| Ramo | Criterio "Póliza Nueva" | Criterio "Póliza Subsecuente" |
|------|------------------------|-------------------------------|
| **GMM** | AÑO_APLI = año actual y recibo coincide con FECINI | Clasificada T-1 con pagos en año actual |
| **Vida Individual** | FECINI en año actual + % Comisión ≥ 2.1% (prima básica) | FECINI en T-1 con pagos en año actual |

#### Reglas Especiales – Vida Individual:
- **Prima Básica vs. Excedente:** Se calcula `% Comisión = Comisión / Prima Neta`
  - ≥ 2.1% → Prima básica (computa al promotor) ✅
  - < 2.1% → Prima excedente (NO computa) ❌
- **Póliza Estándar:** El número de póliza puede variar entre reportes (con/sin ceros, con/sin sufijo `-NNN`), se requiere normalización
- **Reexpediciones:** Pólizas nuevas tienen terminación `00`; al reexpedirse cambian a `NN+1`. Dificultad para rastrearlas

#### Alertas Identificadas en el Procedimiento:
- ⚠️ Pagos del 2-5 de enero pueden pertenecer al año anterior
- ⚠️ Pólizas reexpedidas (terminación `NN+1`) no tienen un método claro de identificación
- ⚠️ Se sugiere cruzar con el deudor por primas de MIT para canceladas/caducadas/no tomadas

---

### 1.2 Procedimiento de Revisión de Indicadores AXA

**Archivo:** `Procedimiento_Revision_Indicadores_AXA.docx`

**Propósito:** Validar los indicadores oficiales que AXA envía mensualmente contra la base interna de la promotoría.

#### Flujo del Proceso:
```
AXA envía indicadores (WhatsApp) → Área de análisis → Cruce con base interna → Identificación de diferencias → Reporte
```

#### Hojas Clave del Reporte AXA:

| Hoja | Contenido |
|------|-----------|
| **Detalle** | Resumen de KPIs por promotor (pólizas, primas, asegurados) |
| **detalle_pol** | Detalle por póliza y asegurado que AXA considera como "nuevo" |

#### KPIs Monitoreados:

| KPI | Ramo | Método de Medición |
|-----|------|--------------------|
| Pólizas Equivalentes Primer Año | Vida Individual | Conversión a MN de pólizas pagadas |
| Prima Primer Año | Vida Individual | Suma prima básica de pólizas nuevas |
| Pólizas Primer Año | GMM | Pólizas pagadas en periodo de análisis |
| Asegurados Primer Año | GMM | Asegurados sin reconocimiento antigüedad AXA Individual |
| Prima Primer Año | GMM | Suma prima de pólizas nuevas pagadas |

#### Criterio de Validación GMM:
- Un asegurado es "nuevo" si:
  - Ha sido **pagado en el periodo de análisis**, Y
  - **No trae reconocimiento de antigüedad AXA Individual**, Y
  - La **antigüedad AXA = fecha inicio de vigencia** de la póliza

#### Problemas Detectados:
- ⚠️ AXA a veces incluye pólizas con reconocimiento de antigüedad que NO deberían contar
- ⚠️ Los reportes son a **mes vencido** (ej: indicadores de octubre llegan a finales de noviembre)
- ⚠️ En el archivo interno `POLIZAS01`, se marca 1=nueva cuando FECINI = Antigüedad AXA, y 0 cuando no

---

## 2. Análisis de Bases de Datos

### 2.1 POLIZAS01 (Base Operativa)

**Archivo:** `POLIZAS01_19022026 (1).xlsx` — *3.4 MB*

| Hoja | Registros | Descripción |
|------|-----------|-------------|
| `querys` | 10,318 | Base completa de consultas (todas las pólizas) |
| `VIDA` | 451 | Pólizas de Vida Individual filtradas |
| `GMM` | 2,677 | Pólizas de Gastos Médicos filtradas |

#### Estructura de Datos (56 columnas):
```
ID | VERSION | AGENTE | ARCHIVO_PDF | ASEGS | ASEGURADO | CC | CESION | COASEGURO | 
CONDICIONES | CONTRATANTE | CP | DEDUCIBLE | DERECHO | DESCFAM | DOMCONTRA | ENDOSO | 
FECEMI | FECFIN | FECINI | FP | GAMA | IVA | MATERNIDAD | MON | NOMRAMO | NOTA | 
PLAN | PLAZOPAGO | POLIZA | PRIMA_TOT | PRIMANETA | RAMO | RECARGO | RED | REGISTRO | 
RFC | SOLICITUD | STATUS | SUMA | TABULADOR | TEL | TIPPAG | TOPE | ZONA | MIGRADA | 
REN | COBERTURA | EMAIL | FECIMPRE | NUEVA | INCSUM | PRIINCSUM | PLASEG | PRIADI | MYSTATUS
```

#### Campos Clave para Análisis:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `POLIZA` | Número de póliza | `0076384A`, `10007U00` |
| `AGENTE` | Código de agente | `47968`, `627523` |
| `NOMRAMO` | Nombre del ramo | `VIDA`, `GASTOS MEDICOS MAYORES INDIVIDUAL` |
| `PLAN` | Producto | `VIDA Y AHORRO`, `FLEX PLUS` |
| `FECINI` | Fecha inicio vigencia | `2024-08-08` |
| `FECFIN` | Fecha fin vigencia | `2056-08-08` |
| `PRIMA_TOT` | Prima total | `28077` |
| `PRIMANETA` | Prima neta | `28077` |
| `STATUS` | Estado del recibo | `PAGADA`, `CANC/X F.PAGO`, `CANC/X SUSTITUCION` |
| `MYSTATUS` | Estado interno | `CANCELADA NO TOMADA`, `CANCELADA CADUCADA`, `PAGADA TOTAL`, `TERMINADA` |
| `NUEVA` | Flag nueva (1/0) | `1` = nueva, `0` = no nueva |
| `FP` | Forma de pago | `MENSUAL`, `ANUAL` |
| `GAMA` | Gama del producto | `ZAFIRO`, `DIAMANTE`, `ESMERALDA` |
| `SUMA` | Suma asegurada | `1000000.00`, `31500000` |
| `TIPPAG` | Tipo de pago | `CARGO AUTOMATICO`, `Tarjeta`, `Agente` |

#### Observaciones:
- Los registros de **Vida** son predominantemente del plan **"MI PROYECTO R / PLAN PERSONAL DE RETIRO"** con registro CNSF `CNSF-S0048-0440-2011`
- Los registros de **GMM** son del plan **"FLEX PLUS"** con gamas variadas (Zafiro, Diamante, Esmeralda) y registro CNSF `CNSF-S0048-0327-2024` / `CNSF-S0048-0427-2024`
- Existen pólizas con diversos estados de cancelación que deben ser filtradas

---

### 2.2 Reporte Maestro (Base Vida y GMM)

**Archivo:** `Reporte 19 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO.xlsm` — *103 MB*

Este es el **archivo central de trabajo** de la promotoría. Contiene **57 hojas** organizadas en:

#### Categorías de Hojas:

| Categoría | Hojas | Propósito |
|-----------|-------|-----------|
| **Conciliaciones** | `CONCILIACIÓN JUL IND 2025 VIDA`, `CONC JUL IND 2025 GMM`, `CONC JULIO IND 2025 VIDA` | Cruce entre base interna e indicadores AXA |
| **Resúmenes** | `RESUMEN VIDA Y GMM`, `RESUMEN POR AGENTE`, `RESUMEN CON GMM`, `RESUMEN SIN GMM`, `RESUMEN VIDA`, `RESUMEN GMM`, `RESUMENES LINEAS PERSONALES` | Dashboards ejecutivos |
| **Indicadores AXA** | `INDICADORES 2024`, `IND JUNIO 2024`, `IND 2025 JUN`, `IND 2025 JUL`, `IND HAST AGOS 2025` | Reportes oficiales de AXA por periodo |
| **Detalle por Póliza** | `DET 2024`, `DET 2025`, `DET JUN 2025`, `DET JUL 2025`, `DET POL 2025` | Registro granular de pólizas |
| **Diferencias** | `DIF JUNIO Y JULIO 2024`, `DIFERENCIA JUNIO Y JULIO 2024`, `DIFERENCIAS VS IND JULIO` | Discrepancias identificadas |
| **Producción** | `Producción vida 2022`, `POLIZAS VIDA 2024`, `POLIZAS VIDA 2025 2.0`, `PRIMA PAGADA` | Seguimiento de producción histórica |
| **Operativo** | `ConcentradoDiario`, `directorio agentes`, `Gestion`, `AUTOMATICO`, `AUTOMATICO VIDA`, `CARTERA GMM` | Gestión diaria, cartera, directorio |
| **Otros** | `RECLUTA PRODUCTIVA`, `NOTIFICACIONES`, `SOLICITACION`, `METAS 2025`, `VERIFICACION GMM 2025` | Reclutamiento, metas, verificaciones |

#### Estructura de Conciliaciones (Hoja principal):
```
Agente | Agts | Nombre Completo | Rol | Situacion | Fecha de Alta | 
Fecha de Rehabilitación | Fecha de Cancelación | Causa de Cancelación | 
Territorio | Oficina | Gerencia | Promotor | Nombre Promotoría | CC
```

#### Estructura de Detalle:
```
poliza | agente | nombre_com | territorio | oficina | gerencia | 
cc | cc_tit | nom_agrup | ramo | cnt | pol_vigente | LARGO | POLIZA | REPETIDAS
```

---

### 2.3 Base Original Histórica (Diciembre)

**Archivo:** `original base de VIDA Y GMM_DIC (VF3DIC)HF (1).xlsx` — *173 MB*

Contiene **31 hojas** con datos históricos desde 2023:

| Categoría | Hojas |
|-----------|-------|
| **Indicadores históricos** | `INDICADORES 2023`, `INDICADORES 2024`, `IND AGENTE MARZO 2025`, `IND MAYO`, `INDICADORES 2025 ABRIL` |
| **Detalle indicadores** | `IND DETALLE MARZO ASEG 2025`, `DETALLE IND MARZO 2025`, `DET IND JUNIO 2025`, `DET IND DICIEMBRE 2023`, `DET IND DICIEMBRE 2024` |
| **Automatización** | `AUTOMATICO GMM`, `AUTOMATICO VIDA`, `AUTOMATICO VIDA2`, `AUTOMATICO VIDA 2024` |
| **Datos fijos y catálogos** | `DATOS FIJOS`, `DATOS FIJOS AUTOMATICO`, `DATOS FIJOS DE VIDA`, `DIRECTORIO`, `DIRECTORIO_RESPALDO` |
| **Producción** | `PRIMA PAGADA`, `PRIMA PAGADA AUTOS`, `CONCENTRADO COMP`, `DATA concentrado 26 OCT 2025` |
| **Deudor** | `DEUDOR 4 JULIO 2025 MAS COL` |

---

### 2.4 Oferta de Valor

**Archivo:** `Oferta_valor_12_63931 (1).xlsb` — *4.1 MB*

Formato binario Excel (.xlsb). Probablemente contiene la propuesta comercial o el catálogo de productos/servicios que la promotoría ofrece. No se pudo leer sin la librería `pyxlsb`.

---

## 3. Diagrama del Proceso de Negocio

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROMOTORÍA MAG – AXA SEGUROS                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────────┐     │
│  │ Sistema  │───▶│  POLIZAS01    │───▶│ Clasificación        │     │
│  │ AXA/MIT  │    │  (querys,     │    │ Nueva / Subsecuente  │     │
│  │          │    │  VIDA, GMM)   │    │ Básica / Excedente   │     │
│  └──────────┘    └───────────────┘    └──────────┬───────────┘     │
│                                                   │                 │
│  ┌──────────┐    ┌───────────────┐               ▼                 │
│  │ AXA envía│───▶│ Indicadores   │    ┌──────────────────────┐     │
│  │ vía      │    │ Oficiales AXA │───▶│ CONCILIACIÓN         │     │
│  │ WhatsApp │    │ (Detalle +    │    │ Base interna vs AXA  │     │
│  └──────────┘    │  detalle_pol) │    └──────────┬───────────┘     │
│                  └───────────────┘               │                 │
│                                                   ▼                 │
│                                        ┌──────────────────────┐     │
│                                        │ Reporte Diferencias  │     │
│                                        │ + Resúmenes          │     │
│                                        │ + KPIs               │     │
│                                        └──────────────────────┘     │
│                                                                     │
│  KPIs: Pólizas Equivalentes | Prima 1er Año | Asegurados Nuevos   │
│  Ramos: Vida Individual | GMM Individual                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Hallazgos y Oportunidades

### 🔴 Problemas Identificados

| # | Problema | Impacto | Archivo/Fuente |
|---|----------|---------|----------------|
| 1 | **Archivos Excel de 100-170 MB** — operación manual insostenible | Alto riesgo de errores, lentitud, corrupción de archivos | Reporte, Base Original |
| 2 | **Sin método claro para rastrear reexpediciones** (terminación `NN+1`) | Posible sub/sobre reporte de pólizas nuevas | Procedimiento Pólizas |
| 3 | **Inconsistencia en formato de número de póliza** entre reportes AXA | Falsos negativos en cruces/conciliaciones | Procedimiento Indicadores |
| 4 | **Indicadores a mes vencido** — AXA puede incluir pólizas que no deberían contar | Diferencias permanentes en métricas | Procedimiento Indicadores |
| 5 | **57 hojas en un solo archivo .xlsm** — exceso de complejidad | Difícil mantenimiento, propenso a errores de macros | Reporte Maestro |
| 6 | **Proceso de recepción vía WhatsApp** | Sin trazabilidad formal, riesgo de pérdida/retraso | Procedimiento Indicadores |

### 🟢 Oportunidades de Automatización

| # | Oportunidad | Beneficio | Prioridad |
|---|-------------|-----------|-----------|
| 1 | **Normalizar números de póliza** ("Póliza Estándar") automáticamente | Eliminar discrepancias en cruces | 🔴 Alta |
| 2 | **Automatizar clasificación Nueva/Subsecuente** con reglas definidas | Reducir tiempo manual y errores | 🔴 Alta |
| 3 | **Automatizar cálculo % Comisión** para Vida (básica vs. excedente) | Eliminar clasificación manual | 🟡 Media |
| 4 | **Dashboard de conciliación automática** vs. indicadores AXA | Reducir de horas a minutos | 🔴 Alta |
| 5 | **Migrar de Excel 170MB a base de datos** (SQLite/PostgreSQL) | Rendimiento, integridad, escalabilidad | 🟡 Media |
| 6 | **Sistema de alertas** para pagos de enero (frontera de año) | Evitar errores de periodo | 🟢 Baja |

---

## 5. Resumen de Métricas Actuales

| Métrica | Vida Individual | GMM |
|---------|----------------|-----|
| **Total pólizas en base** | 451 | 2,677 |
| **Registros totales (querys)** | — | — |
| **Base completa** | 10,318 registros | (incluidos en querys) |
| **Planes principales** | Mi Proyecto R / PPR, Vida y Ahorro | Flex Plus (Zafiro, Diamante, Esmeralda) |
| **Formas de pago** | Cargo automático, Mensual, Anual | Mensual, Anual, Tarjeta, Agente |
| **Periodos cubiertos** | 2022–2026 | 2024–2026 |

---

*Análisis generado el 23 de febrero de 2026.*
