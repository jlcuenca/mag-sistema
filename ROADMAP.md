# 🗺️ ROADMAP — MAG Sistema
## Promotoría MAG · AXA Seguros México
> Generado: 2026-03-02 | Basado en análisis de 17 archivos en `/ref`

---

## 📁 Inventario de Archivos de Referencia Analizados

| # | Archivo | Tipo | Contenido | Filas | Impacto |
|---|---------|------|-----------|-------|---------|
| 1 | `POLIZAS_01_08022026.xlsx` | Data | Cartera completa de pólizas (Vida, GMM, Auto) | 9,997 | ✅ Ya importado |
| 2 | `PAGTOTAL_08022026.xlsx` | Data | **Historial completo de pagos/recibos** | 160,822 | 🔴 Sin importar |
| 3 | `Concentrado2026-02-27.csv` | Data | **Pipeline de solicitudes AXA** (trámite → emisión) | 232 | 🔴 Sin importar |
| 4 | `Concentrado_UltEtapas2026-02-27.xlsx` | Data | **Tracking de etapas por solicitud** | 3,937 | 🔴 Sin importar |
| 5 | `Reporte 08 FEBRERO 2026 BASE...xlsm` | Ref | Base macro Excel Vida+GMM (107MB) — fuente original | — | 📚 Referencia |
| 6 | `original base de VIDA Y GMM_DIC...xlsx` | Ref | Base histórica diciembre (181MB) | — | 📚 Referencia |
| 7 | `Oferta_valor_12_63931.xlsb` | Ref | **Oferta de valor AXA** (comisiones, beneficios) | — | 🟡 Pendiente |
| 8 | `EJEMPLO ESTATUS.xlsx` | Regla | Catálogo de estatus y reglas MyStatus | 8 | 📚 Referencia |
| 9 | `EJEMPLO NUEVA NO NUEVA FORM.xlsx` | Regla | Reglas para clasificar Nueva vs No Nueva con fórmulas | — | 📚 Referencia |
| 10 | `POLIZAS NUEVAS O NO NUEVAS.xlsx` | Regla | Ejemplos de clasificación Nueva/Cancelada | — | 📚 Referencia |
| 11 | `Ejemplos Baja de Asegs y Canceladas.xlsx` | Regla | Reglas de baja de asegurados y cancelaciones | — | 🟡 Pendiente |
| 12 | `Ejemplos Nueva _ Form No Nueva.xlsx` | Regla | Más casos de prueba para reglas | — | 📚 Referencia |
| 13 | `EJEMPLO CAMBIO DE FORMA DE PAGO...xlsx` | Regla | **Endosos y cambios de forma de pago** | 89 | 🟡 Pendiente |
| 14 | `PRIMAPAGADATOTAL (4).xlsx` | Ref | Resumen de prima pagada por ramo | 12 | 📚 Referencia |
| 15 | `Paso a Paso Resultados Finales.docx` | Doc | **Definición de KPIs del dashboard ejecutivo** | 3 tablas | 🟡 Implementar |
| 16 | `WhatsApp Image...PM.jpeg` | Img | **Tabla de Año de Intermediación 2025** (requisitos Beta) | — | 🟡 Pendiente |
| 17 | `YUUM.pptx` | Pres | Presentación YUUM (contexto externo) | — | ℹ️ Informativo |

---

## 🎯 Resumen Ejecutivo

Del análisis de los archivos de referencia se identifican **4 grandes bloques de funcionalidad** que aún no están implementados en MAG Sistema:

1. **📊 Integración de Pagos** — 160K registros de pagos sin importar (PAGTOTAL)
2. **📋 Pipeline de Solicitudes Real** — Datos de 232 solicitudes AXA + 3,937 etapas de tracking
3. **📈 Dashboard Ejecutivo con KPIs Reales** — Fórmulas definidas en el docx "Paso a Paso"
4. **👤 Gestión de Agentes con Modelo Beta** — Tabla de intermediación y oferta de valor

---

## 🚀 FASE 1: Integración de Pagos (Prioridad ALTA)
> **Fuente**: `PAGTOTAL_08022026.xlsx` (160,822 filas)
> **Impacto**: Mejora 80% de precisión en dashboards de cobranza y finanzas

### 1.1 Importador de Recibos/Pagos
**Descripción**: Importar la tabla completa de pagos (`PAGTOTAL`) al modelo `Recibo` existente.

| Campo PAGTOTAL | Campo DB | Descripción |
|---|---|---|
| `AGENTE` | `agente_codigo` | Código de agente |
| `MON` | `moneda` | Moneda (MN, UDIS, USD) |
| `RAMO` | `ramo` | Nombre del ramo |
| `CONTRATANTE` | `contratante` | Nombre del contratante |
| `POLIZA` | `poliza` | Número de póliza |
| `ENDOSO` | `endoso` | Número de endoso |
| `PERINI` | `periodo_inicio` | Período de inicio |
| `FECAPLI` | `fecha_aplicacion` | Fecha de aplicación del pago |
| `COMPROBANTE` | `comprobante` | Número de comprobante |
| `FILLER1` | `filler` | Campo auxiliar |
| `NETA` | `prima_neta` | Prima neta del recibo |
| `PRITOT` | `prima_total` | Prima total del recibo |

**Tareas**:
- [ ] Script `reimportar_pagos.py` similar a `reimportar_polizas.py`
- [ ] Vincular pagos a pólizas via número de póliza (JOIN)
- [ ] Recalcular `prima_acumulada_basica` con datos reales (no estimados)
- [ ] Actualizar `flag_pagada` basado en pagos reales
- [ ] Endpoint API: `POST /importar/excel-pagos`

### 1.2 Dashboard de Cobranza con Datos Reales
**Descripción**: Actualizar los KPIs de cobranza usando los pagos importados.

- [ ] % Cobranza = Σ pagos recibidos / Σ primas emitidas
- [ ] Antigüedad de deuda: días entre `fecha_emision` y hoy sin pago
- [ ] Semáforo recalculado con datos de PAGTOTAL reales
- [ ] Monto cobrado desglosado por mes

### 1.3 Conciliación AXA con Detalle de Pagos
**Descripción**: Cruzar pólizas del POLIZAS_01 con pagos del PAGTOTAL automáticamente.

- [ ] Match por número de póliza: encontrar pagos faltantes
- [ ] Detectar pagos sin póliza asociada (errores AXA)
- [ ] Resumen de diferencias por agente y ramo
- [ ] Exportar reporte de conciliación a Excel

**Estimación**: 5-7 días de desarrollo

---

## 🚀 FASE 2: Pipeline de Solicitudes Real (Prioridad ALTA)
> **Fuente**: `Concentrado2026-02-27.csv` (232 solicitudes, 60 cols) + `Concentrado_UltEtapas2026-02-27.xlsx` (3,937 eventos)
> **Impacto**: Tracking completo del ciclo solicitud → emisión → pago

### 2.1 Importador de Concentrado AXA
**Descripción**: Importar el concentrado de solicitudes de AXA al módulo de solicitudes existente.

| Campo Concentrado | Campo DB | Descripción |
|---|---|---|
| `NoSol` | `folio` | Número de solicitud AXA |
| `Ramo` / `Subramo` | `ramo` | Ramo y subramo |
| `Contratante` | `contratante_nombre` | Nombre del contratante |
| `Producto` | `plan` | Producto solicitado |
| `Forma_Pago` | `forma_pago` | Forma de pago solicitada |
| `Estatus` | `estado` | Estado actual de la solicitud |
| `Etapa` / `SubEtapa` | `etapa`, `sub_etapa` | Etapa del flujo AXA |
| `No_Poliza` | `poliza_emitida` | Póliza generada (si aplica) |
| `F_Captura_Ag` | `fecha_captura` | Fecha de captura por agente |
| `F_Recepcion` | `fecha_recepcion` | Fecha de recepción AXA |
| `F_Envio_poliza` | `fecha_envio_poliza` | Fecha de envío de póliza |
| `Revires` | `num_revires` | Cantidad de devoluciones |
| `PRIMA_CON` | `prima_estimada` | Prima contratada |
| `COM_TOT` | `comision_total` | Comisión total |
| `PRI_PAG` | `prima_pagada` | Prima pagada |
| `Id_Agente_Registro` | `agente_id` | Agente que registró |
| `Promotor` / `id_Promotor` | `promotor` | Promotor asignado |
| `Territorio` / `Zona` / `Oficina` | `territorio` | Datos geográficos |

**Tareas**:
- [ ] Ampliar modelo `Solicitud` con campos del Concentrado
- [ ] Script `importar_concentrado.py`
- [ ] Endpoint API: `POST /importar/concentrado-solicitudes`

### 2.2 Timeline de Etapas por Solicitud
**Descripción**: Importar el historial de `Concentrado_UltEtapas` para mostrar un timeline visual.

Etapas AXA detectadas (3,937 registros):
```
POLIZA_ENVIADA          2,697  (68.5%)
RECHAZO_EMISION           455  (11.6%)
RECHAZO_EXPIRACION        402  (10.2%)
LIBERACION_EMISION         90  ( 2.3%)
INFO_AD_EMISION            84  ( 2.1%)
LIBERACION_SELECCION       81  ( 2.1%)
EMISION                    47  ( 1.2%)
CANCELADO                  29  ( 0.7%)
RECHAZO_SELECCION          25  ( 0.6%)
RECHAZO_AUT_INFO_AD        13  ( 0.3%)
INFO_AD_SELECCION          11  ( 0.3%)
SELECCION                   3  ( 0.1%)
```

- [ ] Modelo `EtapaSolicitud` (nosol, etapa, fecha_etapa, observaciones)
- [ ] Vista timeline vertical en detalle de solicitud
- [ ] KPIs: Tiempo promedio por etapa, % rechazos, tasa de conversión
- [ ] Alerta de solicitudes "atoradas" (>15 días en misma etapa)

### 2.3 Dashboard de Pipeline Mejorado
- [ ] Kanban con datos reales del Concentrado AXA
- [ ] Funnel de conversión: Selección → Emisión → Póliza Enviada → Pagada
- [ ] SLA tracking: Medir `F_Fin_SLA` vs `F_Envio_poliza`
- [ ] Métricas por agente: tasa de rechazo, velocidad de trámite
- [ ] Vincular solicitudes con pólizas emitidas (`No_Poliza` → `poliza_original`)

**Estimación**: 6-8 días de desarrollo

---

## 🚀 FASE 3: Dashboard Ejecutivo con KPIs Formales (Prioridad MEDIA)
> **Fuente**: `Paso a Paso Resultados Finales.docx`
> **Impacto**: Replicar fielmente los reportes ejecutivos que antes se hacían en Excel

### 3.1 Bloque VIDA
Según el docx, los KPIs formales son:

| KPI | Fórmula | Fuente |
|---|---|---|
| N° Pólizas Nuevas VIDA 2024 | COUNT WHERE ramo=VIDA, primer_año=2024, NUEVA=1 | Polizas_01 |
| N° Pólizas Nuevas VIDA 2025 | COUNT WHERE ramo=VIDA, primer_año=2025, NUEVA=1 | Polizas_01 |
| Prima Nueva VIDA 2025 | SUM(prima_neta) WHERE VIDA + nueva + pagada | Polizas_01 + Pagtotal |
| Pólizas Subsecuentes VIDA | COUNT WHERE VIDA + primer_año<2025 + fec_apli=2025 | Polizas_01 |
| Total VIDA 2025 | Suma de nuevas + subsecuentes | Calculado |

### 3.2 Bloque GMM
| KPI | Fórmula | Fuente |
|---|---|---|
| N° Pólizas Nuevas GMM 2024 | COUNT WHERE ramo=GMM, primer_año=2024, NUEVA=1 | Polizas_01 |
| N° Pólizas Nuevas GMM 2025 | COUNT WHERE ramo=GMM, primer_año=2025, NUEVA=1 | Polizas_01 |
| Asegurados nuevos GMM | SUM(num_asegurados) WHERE GMM + nueva | Polizas_01 |
| Prima Nueva GMM 2025 | SUM(prima_neta) WHERE GMM + nueva + pagada | Polizas_01 + Pagtotal |
| Pólizas Subsecuentes GMM | COUNT WHERE GMM + subsecuente | Polizas_01 |

### 3.3 Bloque Metas y Cumplimiento
| KPI | Fuente |
|---|---|
| Meta pólizas nuevas VIDA | Manual (tabla de metas) |
| Meta prima nueva VIDA | Manual |
| Faltante pólizas | Meta - Real |
| % Cumplimiento | Real / Meta × 100 |
| Meta pólizas nuevas GMM | Manual |
| Meta asegurados GMM | Manual |

**Tareas**:
- [ ] Crear tabla `metas` con metas por ramo, año, mes, concepto
- [ ] API endpoint: `GET /dashboard/ejecutivo-formal`
- [ ] Vista ejecutiva con tarjetas de cumplimiento (gauge charts)
- [ ] Comparativo año anterior (2024 vs 2025)
- [ ] Exportar reporte ejecutivo a PDF

**Estimación**: 4-5 días de desarrollo

---

## 🚀 FASE 4: Gestión de Agentes y Modelo Beta (Prioridad MEDIA)
> **Fuente**: `WhatsApp Image 2026-03-01` (Tabla de Intermediación) + `Oferta_valor_12_63931.xlsb`
> **Impacto**: Control de requisitos Beta Productivo y comisiones

### 4.1 Tabla de Año de Intermediación
Según la imagen de referencia de AXA:

| Año Intermediación | Pólizas Nuevas Requeridas | Requisito Vida | Prima Pagada Requerida |
|---|---|---|---|
| Año 1 (Jul 2024 – Dic 2025) | 9 pólizas | Mín 3 de Vida Individual | $200,000 |
| Año 2 (Ene 2023 – Jun 2024) | 12 pólizas | Mín 4 de Vida Individual | $300,000 |
| Año 3 (Ene 2022 – Dic 2022) | 15 pólizas | Mín 5 de Vida Individual | $400,000 |

**Tareas**:
- [ ] Clasificar agentes por año de intermediación
- [ ] Dashboard "Estatus Beta" por agente
- [ ] Semáforo: 🟢 Cumple / 🟡 En riesgo / 🔴 No cumple
- [ ] Alerta de agentes que necesitan X pólizas más para cumplir
- [ ] Proyección: ¿alcanzará la meta al cierre?

### 4.2 Oferta de Valor y Comisiones
**Fuente**: `Oferta_valor_12_63931.xlsb` (Requiere instalar `pyxlsb`)

- [ ] Importar tablas de comisiones por producto
- [ ] Calcular comisión estimada por póliza
- [ ] Proyección de ingreso por agente
- [ ] Comparativo comisiones reales vs tabulador

### 4.3 Directorio de Agentes Enriquecido
Con datos del Concentrado CSV:

- [ ] Territorio, Zona, Oficina, Canal por agente
- [ ] Clasificación: Agentes / Persona Moral / Persona Física
- [ ] Promotor asignado
- [ ] Historial de solicitudes y tasa de conversión

**Estimación**: 5-6 días de desarrollo

---

## 🚀 FASE 5: Endosos y Movimientos (Prioridad BAJA)
> **Fuente**: `EJEMPLO CAMBIO DE FORMA DE PAGO O MOVIMIENTOS A LA PÓLIZA POR ENDOSO.xlsx` (89 registros)

### 5.1 Gestión de Endosos
- [ ] Modelo `Endoso` (poliza, tipo_endoso, fecha, descripción, impacto_prima)
- [ ] Tipos: Cambio forma de pago, Inclusión/Exclusión de asegurados, Ajuste de cobertura
- [ ] Timeline de endosos por póliza (en el drilldown de póliza)
- [ ] Impacto en prima: recalcular prima neta post-endoso

### 5.2 Baja de Asegurados
> **Fuente**: `Ejemplos Baja de Asegs y Canceladas.xlsx`

- [ ] Detectar pólizas con baja de asegurados vs cancelación total
- [ ] Diferenciar: Baja parcial (1 de N asegurados) vs Cancelación total
- [ ] Impacto en prima por baja parcial
- [ ] Alerta de pólizas con historial de bajas frecuentes

**Estimación**: 3-4 días de desarrollo

---

## 🚀 FASE 6: Funciones Transversales (Continuo)

### 6.1 Visor de Documentos PDF ✅
- [x] Proxy backend para PDFs de pólizas
- [x] Proxy backend para PDFs de solicitudes
- [x] Modal embebido con iframe
- [x] URL configurable desde BD

### 6.2 Motor de Importación Unificado
- [ ] Interfaz drag & drop para subir archivos
- [ ] Auto-detección del tipo de archivo (POLIZAS, PAGTOTAL, CONCENTRADO)
- [ ] Validación pre-importación (vista previa de cambios)
- [ ] Log de importaciones con diff (qué cambió)
- [ ] Importación incremental (no borrar todo cada vez)

### 6.3 Reportes y Exportaciones
- [ ] Exportar dashboard ejecutivo a PDF
- [ ] Reporte mensual automático (email o descarga)
- [ ] Exportar cualquier tabla filtrada a Excel
- [ ] Gráficas exportables como imágenes

### 6.4 Notificaciones y Alertas
- [ ] Alertas de renovaciones próximas (30/60/90 días)
- [ ] Alertas de pólizas en riesgo de cancelación
- [ ] Alerta de agentes que no cumplen meta Beta
- [ ] Notificación de nuevas pólizas emitidas

---

## 📅 Timeline Propuesto

```
MARZO 2026
├── Semana 1 (Mar 3-7)   → FASE 1.1: Importador de Pagos (PAGTOTAL)
├── Semana 2 (Mar 10-14) → FASE 1.2-1.3: Cobranza real + Conciliación
├── Semana 3 (Mar 17-21) → FASE 2.1-2.2: Concentrado + Etapas
└── Semana 4 (Mar 24-28) → FASE 2.3: Pipeline mejorado

ABRIL 2026
├── Semana 1 (Abr 1-4)   → FASE 3: Dashboard Ejecutivo formal
├── Semana 2 (Abr 7-11)  → FASE 4.1: Modelo Beta + Intermediación
├── Semana 3 (Abr 14-18) → FASE 4.2-4.3: Comisiones + Directorio
└── Semana 4 (Abr 21-25) → FASE 5 + FASE 6: Endosos + Mejoras UX

MAYO 2026
├── UAT y ajustes finales
└── Go-live producción completa
```

---

## 📊 Métricas de Éxito

| Métrica | Actual | Objetivo Fase 1 | Objetivo Final |
|---|---|---|---|
| Pólizas importadas | 9,997 | 9,997 | 10,000+ |
| Pagos/Recibos importados | 0 | **160,822** | 160,822+ |
| Solicitudes con tracking | 0 | **232** | 500+ |
| Eventos de etapa | 0 | **3,937** | 5,000+ |
| Precisión % Cobranza | ~66% (estimado) | **Real (calculado)** | Real |
| Agentes con perfil Beta | 0 | 0 | **197** |
| Tiempo generación reporte | Manual (2h) | 5 min | **Automático** |

---

## 🏗️ Dependencias Técnicas

| Fase | Backend | Frontend | BD |
|---|---|---|---|
| Fase 1 | Nuevo endpoint importar pagos | Actualizar cobranza | Modelo `Recibo` expandido |
| Fase 2 | Endpoint concentrado + etapas | Pipeline Kanban real | Modelos `Solicitud` expandido + `EtapaSolicitud` |
| Fase 3 | Endpoint ejecutivo-formal | Dashboard ejecutivo v2 | Tabla `Metas` |
| Fase 4 | Endpoint perfil-beta | Dashboard agente individual | Tabla `PerfilBeta` |
| Fase 5 | CRUD endosos | Timeline en drilldown | Modelo `Endoso` |
| Fase 6 | Mejoras generales | UX/Export | — |

---

*Documento vivo — actualizar conforme se complete cada fase.*
*MAG Sistema v0.2.0 | Promotoría MAG · AXA Seguros México*
