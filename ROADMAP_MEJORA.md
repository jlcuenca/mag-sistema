# 🗺️ Roadmap de Mejora — MAG Sistema

**Promotoría de Seguros AXA · Ramos Vida Individual y GMG Individual**  
**Fecha de análisis:** 24 de febrero de 2026  
**Versión actual:** v0.1.0 MVP (FastAPI + Next.js + SQLite)

---

## 📊 Resumen Ejecutivo

Se analizaron **7 archivos** en el folder `fuentes/` que representan las nuevas fuentes de información proporcionadas por el equipo operativo de la promotoría MAG. Estos archivos revelan **3 dimensiones de mejora** no contempladas en el MVP actual:

| Dimensión | Archivos Clave | Impacto |
|-----------|---------------|---------|
| **Dashboard financiero** (Primas: Ingresos vs Egresos) | `DASHBOARD PRIMAS INGRESOS VS EGRESOS.pptx` | Nuevo módulo de seguimiento financiero |
| **Sistema competidor/referencia** (MIGGO) | `MIGGO.pptx` | Blueprint de funcionalidades esperadas por el usuario |
| **Datos reales de producción** (Reporte Cubo 2025) | `Reporte_Cubo_2025_ALL (3).xlsx` | 993 pólizas reales con estructura de datos enriquecida |
| **Catálogo de estatus enriquecido** | `EJEMPLO ESTATUS.xlsx` | 6 estados de póliza (vs. 3 actuales) |
| **Vistas ejecutivas de referencia** | `VISTAS.xlsx`, `VISTAS CUITLAHUAC.xlsx` | Diseño de dashboards gerenciales y operativos |
| **Registro de reunión** | `GMT20260224-*.mp4` | Contexto de sesión de trabajo (477 MB, video) |

---

## 📂 Análisis Detallado por Archivo

### 1. `DASHBOARD PRIMAS INGRESOS VS EGRESOS.pptx` (289 KB, 4 slides)

**Contenido descubierto:**
- **Slide 1:** Portada (sin texto visible, probablemente imagen)
- **Slide 2:** "IDEAL 2026" — Presupuesto y proyección ideal para el año
- **Slide 3:** "Seguimiento Ideal a la Cobranza 2026" — Tracking de cobranza
- **Slide 4:** "Seguimiento Ideal a la Renovación 2026" — Tracking de renovaciones

**Revelaciones:**
- La promotoría necesita un **módulo de proyecciones financieras** que hoy no existe
- Requiere separar **ingresos (primas cobradas)** vs. **egresos (comisiones, gastos operativos)**
- El seguimiento a la **cobranza** y las **renovaciones** son procesos independientes que necesitan vistas propias
- El concepto "IDEAL" sugiere comparación **presupuesto vs. real vs. proyección**

**⇒ Gap identificado:** El MVP no tiene módulo de presupuesto, proyecciones ni seguimiento a cobranza/renovaciones.

---

### 2. `MIGGO.pptx` (323 KB, 8 slides) — ⚠️ CRÍTICO

**Contenido descubierto:**
MIGGO es un **sistema de administración de carteras de seguros** que funciona como referencia competitiva o sistema previo. Sus 8 slides revelan la arquitectura funcional completa que el usuario espera:

| Slide | Módulo | Funcionalidades |
|-------|--------|----------------|
| 1 | **Portada** | "miggo - Sistema para administrar carteras" |
| 2 | **Navegación** | 7 módulos: Contratante, Gestión, Perfiles, Cobranza, Solicitación, Configuración, Póliza |
| 3 | **Configuración** | Alta de agente **por aseguradora** (clave por aseguradora), sub-agentes/vendedores con **distribución de comisiones**, múltiples niveles jerárquicos |
| 4 | **Solicitación** | Solicitudes en trámite, notificaciones, estatus del folio de emisión, vistas por perfiles (aseguradora/agente/promotor) |
| 5 | **Gestión** | Estadísticas y resúmenes de resultados, presupuesto con **proyección de renovaciones**, ingresos |
| 6 | **Contratante** | Datos del contratante/contacto/documentos, relación de pólizas, "Referido por" (sistema de referidos) |
| 7 | **Cobranza** | **Deudor por Prima** (-30 a +30 días), prioridad visual (🔴🟠🟢🟡), datos del recibo (n/m), comisión, monto pagado, **pólizas canceladas** con detalle |
| 8 | **Póliza** | Póliza Madre → Renovación año X → Renovación año Y, sistema de **referidos** |

**Revelaciones críticas:**
1. **Multi-aseguradora:** MIGGO soporta múltiples aseguradoras, no solo AXA. La clave de agente es por aseguradora.
2. **Distribución de comisiones:** Sub-agentes y vendedores con comisiones distribuidas por nivel.
3. **Deudor por Prima:** Vista operativa principal con semáforo de urgencia (-30 a +30 días).
4. **Cadena de pólizas:** Póliza Madre → Renovaciones por año (relación padre-hijo histórica).
5. **Sistema de referidos:** Tracking de quién refirió a cada contratante.
6. **Solicitudes:** Tracking del flujo de emisión (folio → trámite → emitida).

**⇒ Gap identificado:** El MVP actual carece de 12+ funcionalidades que MIGGO ya ofrece.

---

### 3. `Reporte_Cubo_2025_ALL (3).xlsx` (435 KB) — ⚠️ DATOS REALES

**Estructura descubierta — 3 hojas (generadas el 24/02/2026, el mismo día):**

#### Hoja RESUMEN (145 filas × 15 columnas)
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| CLAVE AGENTE | Código | `56917`, `647749` |
| NOMBRE COMPLETO | Nombre del agente | `PREAVISIO AGENTE DE SEGUROS, S.A. DE C.V.` |
| SEGMENTO | Clasificación comercial | `ALFA TOP INTEGRAL`, `BETA1`, `OMEGA` |
| GESTION COMERCIAL | Líder/gestión | `ALFA/MARIA ESTHER`, `MARIO FLORES` |
| LIDER | Código Líder | `63931` (todos) |
| POLIZAS ANTERIOR/ACTUAL | Comparativo año anterior vs actual | `46` → `41` |
| ASEGURADOS ANTERIOR/ACTUAL | Comparativo asegurados | `53` → `50` |
| VENTA NUEVA ANTERIOR/ACTUAL | Prima venta nueva | `$1,103,941` → `$1,154,580` |
| SUBSECUENTE ANTERIOR/ACTUAL | Prima subsecuente | `$152,904` → `$203,497` |
| TOTAL ANTERIOR/ACTUAL | Total prima | `$1,256,846` → `$1,358,077` |

**Totales globales:**
- **140 agentes** con producción
- **Prima neta total:** $18,277,686.51
- **Pólizas:** 830 (anterior) → 1,032 (actual)
- **Asegurados:** 982 → 1,032

#### Hoja GENERAL (998 filas × 25 columnas)
| Nuevos campos descubiertos | Descripción |
|----------------------------|-------------|
| **SEGMENTO** | `ALFA TOP INTEGRAL`, `BETA1`, `BETA2`, `OMEGA`, `ALFA TOP COMBINADO`, `ALFA INTEGRAL` |
| **CLASIFICACION** | `CY SUBSECUENTE`, `CY ANUAL` (Ciclo Year) |
| **ESTATUS** | `POLIZA PAGADA`, `POLIZA CANCELADA`, `POLIZA AL CORRIENTE`, `POLIZA ATRASADA` |
| **DETALLE_ESTATUS** | `FALTA DE PAGO`, `NO TOMADA`, `MODIFICACION DE POLIZA (AUMENTO DE PRIMA)`, `MODIFICACION DE POLIZA (REDUCCION DE PRIMA)` |
| **NUEVA_POLIZA** | Flag 1/0 |
| **NETA_TOTAL_CONTRATO** | Prima neta total del contrato |
| **NETA_TOTAL_ACUMULADO** | Prima neta acumulada pagada |
| **NETA_SEGUN_FORMA_PAGO** | Prima calculada según frecuencia |
| **NETA_SIN_FORMA_PAGO** | Prima sin ajuste de forma de pago |
| **NETA_CON_CANCELACION** | Prima con impacto de cancelación |
| **AÑO_CONF** | Año de confirmación |

**993 registros reales de pólizas con datos completos.**

#### Hoja DETALLE (2,555 filas × 24 columnas)
| Nuevos campos descubiertos | Descripción |
|----------------------------|-------------|
| **FECHA_RECIBO** | Fecha del recibo individual |
| **AÑO_APLI** | Año de aplicación del pago |
| **MES_CONF** | Mes de confirmación |
| **AÑO_CONF** | Año de confirmación |
| **COMPROBANTE** | Número de comprobante (`DS175679`, etc.) |
| **NETA_TOTAL_ACUMULADA** | Prima neta acumulada |

**2,550 registros a nivel recibo** (múltiples recibos por póliza).

**⇒ Gap identificado:** El modelo de datos actual no contempla la granularidad a nivel **recibo/pago**, ni los campos de segmento, clasificación CY, comprobante, ni las 5 métricas de prima distintas.

---

### 4. `EJEMPLO ESTATUS.xlsx` (9.6 KB)

**Catálogo completo de estatus de pólizas:**

| Estatus | Descripción | Ejemplo |
|---------|-------------|---------|
| **PENDIENTE DE PAGO** | Póliza emitida dentro de los 30 días de fecha de emisión | `17958V00` |
| **NO TOMADA** | Póliza emitida no pagada dentro de los 30 días siguientes | `17828V00` |
| **AL CORRIENTE** | Póliza que tiene pagados las fracciones que ya inició vigencia | — |
| **ATRASADA** | Póliza dentro de los 30 días de un recibo diferente al 1er recibo | `16784U00` |
| **CANCELADA** | Póliza que no pagó dentro de los 30 días un recibo de las fracciones | `18104U00` |
| **REHABILITADA** | Póliza pagada después de 31 días después de inicio de vigencia | — |

**⇒ Gap identificado:** El MVP actual solo maneja 3 estatus (`PAGADA`, `CANC/X F.PAGO`, `CANC/X SUSTITUCION`). El Reporte Cubo usa un sistema de **6 estatus + detalle**, lo que requiere ampliar la lógica de `calcular_mystatus()` en `rules.py`.

---

### 5. `VISTAS.xlsx` (12 KB) — Vista Ejecutiva Directiva

**Dashboard diseñado por el usuario para nivel directivo:**

**Panel GMM (Gastos Médicos):**
| KPI | 2024 | 2025 | Variación |
|-----|------|------|-----------|
| N° Pólizas Nuevas | 653 | 672 | +2.91% |
| Asegurados | 1,029 | 1,019 | -0.97% |
| Prima GMM Venta Nueva | $14,205,738 | $15,054,843 | +5.98% |
| Prima Subsecuente GMM | $1,968,985 | $2,631,796 | +33.66% |
| **Total GMM** | **$16,174,723** | **$17,686,639** | **+9.35%** |

**Panel Vida:**
| KPI | 2024 | 2025 | Variación |
|-----|------|------|-----------|
| N° Pólizas Nuevas | 287 | 260 | -9.41% |
| Equivalentes | 386 | 361.5 | -6.35% |
| Prima Vida Venta Nueva | $13,184,225 | $16,841,996 | +27.74% |
| Prima Subsecuente Vida | $4,897,379 | $3,990,498 | -18.52% |
| **Total Vida** | **$18,081,605** | **$20,832,495** | **+15.21%** |

**Filtros requeridos:** Por ramo, por promotor, por líder, por gestión comercial, por segmento, por agente.
**Niveles de vista:** Dirección, Gerencial, Administrativo, Top 10, Top 20.

**Panel adicional:** Comparativo mes X-1 vs mes X, acumulado al mes, variación, presupuesto, variación vs presupuesto.

---

### 6. `VISTAS CUITLAHUAC.xlsx` (28 KB) — Vista Gerencial + Operativa

**Hoja `RESUMENES GERENCIAL` (63 filas × 20 columnas):**
- Mismo esquema que VISTAS.xlsx pero con **Resumen Gerencial** expandido
- Incluye campo de **Presupuesto** y **variación vs. presupuesto**

**Hoja `OPERATIVO` (37 filas × 47 columnas) — ⚠️ LA MÁS RICA:**

Contiene **47 columnas** con el desglose completo por agente incluyendo:

| Grupo de Campos | Columnas |
|-----------------|----------|
| **Identidad** | CLAVE, AGENTE, SEGMENTO, ESTADO, ASOCIADO, SEGMENTO AGRUPADO, GESTIÓN |
| **Vida actual** | PÓLIZAS VIDA, EQUIV, PRIMA PAGADA VIDA |
| **GMM actual** | PÓLIZAS GMM, ASEG, PRIMA PAGADA GMM |
| **Total** | PRIMA PAGADA TOTAL |
| **Metas** | META PÓLIZAS/EQUIV, FALTANTE, META AXA PRIMA VIDA, FALTA PRIMA, META JANEM PRIMA GMM |
| **GMM comparativo 2024 vs 2025** | Pólizas, Asegurados, Prima venta nueva, Prima subsecuente, Total, Crecimiento |
| **Vida comparativo 2024 vs 2025** | Pólizas, Equivalentes, Prima venta nueva, Prima subsecuente, Total, Crecimiento |

**Nuevo campo descubierto: SEGMENTO AGRUPADO**
| Segmento | Agrupado |
|----------|----------|
| ALFA TOP INTEGRAL | ALFA |
| ALFA TOP COMBINADO | ALFA |
| ALFA INTEGRAL | ALFA |
| ALFA/BETA | ALFA |
| BETA1 | BETA |
| BETA2 | BETA |
| OMEGA | OMEGA |

**⇒ Gap identificado:** El MVP no tiene la dimensión de Segmento (ALFA/BETA/OMEGA), ni el agrupamiento, ni las metas por agente con faltantes calculados, ni el comparativo interanual año vs año.

---

### 7. `GMT20260224-004410_Recording_1920x1080 (3).mp4` (477 MB)

Video de grabación de reunión/pantalla del 24 de febrero de 2026. Contiene contexto de la sesión de trabajo pero no es analizable textualmente.

---

## 🔍 Mapa de Gaps: MVP Actual vs. Necesidades Reales

| # | Funcionalidad Requerida | MVP Actual | Fuente | Prioridad |
|---|------------------------|------------|--------|-----------|
| G1 | **Sistema de 6 estatus** (Pendiente, No Tomada, Al Corriente, Atrasada, Cancelada, Rehabilitada) | Solo 3 estatus | `EJEMPLO ESTATUS.xlsx` | 🔴 Alta |
| G2 | **13 segmentos comerciales** (ALFA TOP, BETA1, OMEGA...) con agrupamiento | No existe | `Reporte_Cubo`, `VISTAS CUITLAHUAC` | 🔴 Alta |
| G3 | **Dashboard comparativo interanual** (2024 vs 2025 con variación %) | Solo 1 año | `VISTAS.xlsx` | 🔴 Alta |
| G4 | **Granularidad a nivel recibo/pago** (2,550 registros de detalle) | Solo nivel póliza | `Reporte_Cubo DETALLE` | 🔴 Alta |
| G5 | **5 métricas de prima distintas** (Total contrato, Acumulada, Según forma pago, Sin forma pago, Con cancelación) | Solo prima_neta y prima_total | `Reporte_Cubo GENERAL` | 🟡 Media |
| G6 | **Metas por agente** con cálculo de faltante | Solo metas globales | `VISTAS CUITLAHUAC` | 🟡 Media |
| G7 | **Presupuesto vs Real vs Proyección** | No existe | `DASHBOARD PRIMAS`, `VISTAS` | 🟡 Media |
| G8 | **Deudor por Prima** con semáforo (-30 a +30 días) | Solo alertas básicas de cartera | `MIGGO.pptx` | 🟡 Media |
| G9 | **Cadena de renovaciones** (Póliza Madre → Renovación año X → Y) | Solo poliza_padre_id para reexpediciones | `MIGGO.pptx` | 🟡 Media |
| G10 | **Módulo de Cobranza** con priorización visual | No existe | `MIGGO.pptx` | 🟡 Media |
| G11 | **Gestión Comercial y Líderes** como dimensión de análisis | No existe | `Reporte_Cubo` | 🟡 Media |
| G12 | **Comprobantes de pago** (número y trazabilidad) | No existe | `Reporte_Cubo DETALLE` | 🟢 Baja |
| G13 | **Módulo de Solicitación** (folio de emisión, trámites) | No existe | `MIGGO.pptx` | 🟢 Baja |
| G14 | **Sistema de Referidos** (quién refirió al contratante) | No existe | `MIGGO.pptx` | 🟢 Baja |
| G15 | **Distribución de comisiones** multi-nivel | No existe | `MIGGO.pptx` | 🟢 Baja |
| G16 | **Multi-aseguradora** (clave por aseguradora) | Solo AXA | `MIGGO.pptx` | 🟢 Futuro |
| G17 | **Seguimiento Cobranza** con proyección | No existe | `DASHBOARD PRIMAS` | 🟡 Media |
| G18 | **Seguimiento Renovaciones** con proyección | No existe | `DASHBOARD PRIMAS` | 🟡 Media |
| G19 | **Importación del Reporte Cubo** (formato real descubierto) | Solo POLIZAS01 | `Reporte_Cubo` | 🔴 Alta |

---

## 🛣️ Roadmap de Mejora — 6 Fases

### FASE 0 · Importación de Datos Reales (Semana 1)
> **Objetivo:** Cargar los 993 registros reales del Reporte Cubo a la BD y validar que el sistema funcione con datos de producción.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **0.1** Extender modelo de datos | Agregar campos: `segmento`, `gestion_comercial`, `lider`, `clasificacion_cy`, `estatus_detalle`, `neta_total_contrato`, `neta_acumulada`, `neta_segun_forma_pago`, `neta_sin_forma_pago`, `neta_con_cancelacion`, `año_conf`, `mes_conf` | 3h | G2, G4, G5 |
| **0.2** Crear tabla `recibos` | Nueva tabla para granularidad a nivel recibo: `poliza_id`, `fecha_recibo`, `año_apli`, `mes_conf`, `año_conf`, `comprobante`, `neta_acumulada`, `neta_forma_pago`, `neta_sin_forma`, `neta_cancelacion` | 3h | G4, G12 |
| **0.3** Importador Reporte Cubo | Endpoint que lea las 3 hojas (RESUMEN, GENERAL, DETALLE) y cargue datos reales | 6h | G19 |
| **0.4** Ampliar catálogo de estatus | Implementar los 6 estatus + detalle de estatus | 2h | G1 |
| **0.5** Seed con datos reales | Reemplazar datos demo con los 993 registros reales | 2h | — |

**Criterio de éxito:** Dashboard principal muestra KPIs reales ($18.2M prima neta, 140 agentes, 1,032 pólizas).

---

### FASE 1 · Dashboard Ejecutivo Real (Semanas 2-3)
> **Objetivo:** Replicar las vistas de VISTAS.xlsx y VISTAS CUITLAHUAC.xlsx en el sistema web.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **1.1** Vista Directiva | Dashboard GMM + Vida con comparativo 2024 vs 2025, variaciones %, filtros por ramo/promotor/líder/gestión/segmento/agente | 8h | G3, G11 |
| **1.2** Vista Gerencial | Comparativo mes X-1 vs mes X, acumulado, presupuesto, variación vs presupuesto | 6h | G7 |
| **1.3** Vista Operativa (47 columnas) | Tabla interactiva con todos los campos de VISTAS CUITLAHUAC OPERATIVO, incluyendo metas y faltantes por agente | 8h | G6 |
| **1.4** Segmentos (ALFA/BETA/OMEGA) | Implementar dimensión de segmento con agrupamiento, gráficas de donut por segmento | 3h | G2 |
| **1.5** Top N dinámico | Selector para Top 10 / Top 20 / Todos, por nivel (Dirección/Gerencial/Admin) | 2h | — |
| **1.6** Selector de periodos | Filtro por día/mes/trimestre/año comparable | 3h | — |

**Criterio de éxito:** Las 3 vistas (Directiva, Gerencial, Operativa) replican exactamente los datos de los Excel con filtrado interactivo.

---

### FASE 2 · Módulo de Cobranza y Deudor (Semanas 4-5)
> **Objetivo:** Implementar el módulo de cobranza inspirado en MIGGO, con priorización visual del deudor por prima.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **2.1** Vista Deudor por Prima | Tabla con semáforo de prioridad: 🔴 Crítico (-30+ días) / 🟠 Urgente (-15 a -30) / 🟡 Atención (0 a -15) / 🟢 Al día (+0 a +30) | 6h | G8 |
| **2.2** Detalle de cobranza | Por póliza: contratante, conducto de cobro, fecha vigencia, recibo n/m, monto al cobro, comisión, monto pagado | 4h | G10 |
| **2.3** Seguimiento a cobranza | Vista de progreso de cobranza por periodo con proyección lineal | 4h | G17 |
| **2.4** Seguimiento a renovaciones | Pólizas próximas a renovar con tracking de estado | 4h | G18 |
| **2.5** Panel de pólizas canceladas | Listado detallado con tipo de cancelación y monto impactado | 3h | G1 |
| **2.6** Alertas automáticas | Notificaciones en dashboard para recibos vencidos, pólizas por cancelar | 2h | — |

**Criterio de éxito:** El analista puede identificar en < 30 segundos los recibos más urgentes de cobrar.

---

### FASE 3 · Modelo de Datos Enriquecido (Semanas 5-6)
> **Objetivo:** Completar las estructuras de datos que soportan las funcionalidades avanzadas.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **3.1** Cadena de renovaciones | Relación Póliza Madre → Renovación Año X → Año Y con trazabilidad histórica completa | 4h | G9 |
| **3.2** Tabla `segmentos` | Catálogo de segmentos (ALFA TOP INTEGRAL, BETA1, OMEGA...) con agrupamiento (ALFA, BETA, OMEGA) | 2h | G2 |
| **3.3** Tabla `metas_agente` | Metas individuales: meta pólizas/equiv, meta prima vida, meta prima GMM, cálculo automático de faltante | 3h | G6 |
| **3.4** Tabla `presupuestos` | Presupuesto mensual/trimestral/anual por ramo y agente, con cálculo de variación vs real | 3h | G7 |
| **3.5** Gestión Comercial como entidad | Tabla `gestiones_comerciales` con líderes y asignación de agentes | 2h | G11 |
| **3.6** Motor de estatus enriquecido | Refactor de `calcular_mystatus()` con los 6 estatus, lógica temporal (30 días), detalle | 3h | G1 |

**Criterio de éxito:** El esquema de BD soporta todas las dimensiones descubiertas en los fuentes.

---

### FASE 4 · Ingresos vs Egresos y Proyecciones (Semanas 7-8)
> **Objetivo:** Implementar el dashboard financiero de Primas: Ingresos vs Egresos descubierto en el PPTX.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **4.1** Dashboard Ingresos vs Egresos | Vista de primas cobradas (ingresos) vs. comisiones pagadas (egresos) con margen operativo | 8h | G7 |
| **4.2** Proyección de cierre | Algoritmo de proyección lineal/tendencial para estimar prima de cierre del ejercicio basado en tendencia actual | 4h | G7 |
| **4.3** Presupuesto "IDEAL 2026" | Ingreso de presupuesto ideal y comparativo automático mensual | 3h | G7 |
| **4.4** Gráficas de tendencia | Líneas de tendencia con bandas de confianza, comparativo año actual vs anterior | 4h | G3 |
| **4.5** Exportación de reportes financieros | PDF/Excel con formato ejecutivo para presentación a dirección | 4h | — |

**Criterio de éxito:** La dirección puede ver en una sola pantalla si la promotoría va por encima o debajo del IDEAL 2026.

---

### FASE 5 · Funcionalidades MIGGO Avanzadas (Semanas 9-12)
> **Objetivo:** Cerrar los gaps funcionales identificados en la presentación de MIGGO.

| Tarea | Descripción | Esfuerzo | Gaps |
|-------|-------------|----------|------|
| **5.1** Módulo Contratante | CRUD de contratantes con datos de contacto, documentos, relación de pólizas, "Referido por" | 8h | G14 |
| **5.2** Módulo Solicitación | Tracking de solicitudes: folio → en trámite → emitida → pagada, notificaciones | 8h | G13 |
| **5.3** Distribución de comisiones | Configuración de sub-agentes/vendedores con distribución porcentual multi-nivel | 6h | G15 |
| **5.4** Perfiles y permisos avanzados | Vistas por perfil: Promotor, Gerente, Agente, Analista — cada uno ve solo lo que le corresponde | 6h | — |
| **5.5** Configuración dinámica | Panel de configuración: umbral comisión, tipos de cambio, catálogos de segmento, estatus | 4h | — |

**Criterio de éxito:** El sistema MAG iguala o supera las capacidades visibles de MIGGO.

---

## 📐 Cambios al Modelo de Datos Requeridos

### Nuevas tablas

```sql
-- Recibos (granularidad a nivel pago)
CREATE TABLE recibos (
    id              SERIAL PRIMARY KEY,
    poliza_id       INTEGER REFERENCES polizas(id),
    fecha_recibo    DATE NOT NULL,
    anio_apli       INTEGER,
    mes_conf        INTEGER,
    anio_conf       INTEGER,
    comprobante     VARCHAR(30),
    neta_acumulada  DECIMAL(14,2),
    neta_forma_pago DECIMAL(14,2),
    neta_sin_forma  DECIMAL(14,2),
    neta_cancelacion DECIMAL(14,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Segmentos comerciales
CREATE TABLE segmentos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,  -- 'ALFA TOP INTEGRAL'
    agrupado        VARCHAR(20) NOT NULL,          -- 'ALFA'
    orden           INTEGER DEFAULT 0
);

-- Presupuestos
CREATE TABLE presupuestos (
    id              SERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    periodo         VARCHAR(7),        -- NULL=anual, '2026-01'=mensual
    agente_id       INTEGER REFERENCES agentes(id),
    meta_polizas_vida   INTEGER,
    meta_equiv_vida     DECIMAL(10,2),
    meta_prima_vida     DECIMAL(14,2),
    meta_polizas_gmm    INTEGER,
    meta_aseg_gmm       INTEGER,
    meta_prima_gmm      DECIMAL(14,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Contratantes
CREATE TABLE contratantes (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(200) NOT NULL,
    rfc             VARCHAR(20),
    telefono        VARCHAR(20),
    email           VARCHAR(200),
    domicilio       TEXT,
    referido_por_id INTEGER REFERENCES contratantes(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Solicitudes (folios de emisión)
CREATE TABLE solicitudes (
    id              SERIAL PRIMARY KEY,
    folio           VARCHAR(30),
    agente_id       INTEGER REFERENCES agentes(id),
    contratante_id  INTEGER REFERENCES contratantes(id),
    ramo            VARCHAR(100),
    estado          VARCHAR(30),  -- TRAMITE, EMITIDA, PAGADA, RECHAZADA
    fecha_solicitud DATE,
    fecha_emision   DATE,
    notas           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### Campos nuevos en `polizas`

```sql
ALTER TABLE polizas ADD COLUMN segmento_id       INTEGER REFERENCES segmentos(id);
ALTER TABLE polizas ADD COLUMN gestion_comercial  VARCHAR(100);
ALTER TABLE polizas ADD COLUMN lider_codigo       VARCHAR(20);
ALTER TABLE polizas ADD COLUMN clasificacion_cy   VARCHAR(30);  -- 'CY SUBSECUENTE', 'CY ANUAL'
ALTER TABLE polizas ADD COLUMN estatus_detalle    VARCHAR(100); -- 'FALTA DE PAGO', 'NO TOMADA', etc.
ALTER TABLE polizas ADD COLUMN neta_total_contrato DECIMAL(14,2);
ALTER TABLE polizas ADD COLUMN neta_acumulada     DECIMAL(14,2);
ALTER TABLE polizas ADD COLUMN neta_forma_pago    DECIMAL(14,2);
ALTER TABLE polizas ADD COLUMN neta_sin_forma     DECIMAL(14,2);
ALTER TABLE polizas ADD COLUMN neta_cancelacion   DECIMAL(14,2);
ALTER TABLE polizas ADD COLUMN anio_conf          INTEGER;
ALTER TABLE polizas ADD COLUMN mes_conf           INTEGER;
ALTER TABLE polizas ADD COLUMN contratante_id     INTEGER REFERENCES contratantes(id);
ALTER TABLE polizas ADD COLUMN poliza_madre_id    INTEGER REFERENCES polizas(id);  -- Para cadena de renovaciones
```

### Campos nuevos en `agentes`

```sql
ALTER TABLE agentes ADD COLUMN segmento_id       INTEGER REFERENCES segmentos(id);
ALTER TABLE agentes ADD COLUMN segmento_agrupado VARCHAR(20);
ALTER TABLE agentes ADD COLUMN gestion_comercial VARCHAR(100);
ALTER TABLE agentes ADD COLUMN lider_codigo      VARCHAR(20);
ALTER TABLE agentes ADD COLUMN estado            VARCHAR(30);  -- 'ACTIVO', '0' (interno)
ALTER TABLE agentes ADD COLUMN asociado          VARCHAR(100); -- Asociación territorial
```

---

## 📊 Métricas de Impacto Estimado

| Métrica | Antes (Excel manual) | Después (MAG Sistema v1.0) | Mejora |
|---------|---------------------|---------------------------|--------|
| Tiempo de conciliación mensual | 4-8 horas | 5-10 minutos | **~97%** |
| Generación de reporte ejecutivo | 2-3 horas | 10 segundos (dashboard) | **~99%** |
| Identificación de deudor urgente | 30-60 min (buscar en Excel 100MB) | < 30 segundos | **~98%** |
| Riesgo de pérdida de datos | Alto (archivos 170MB, corrupción) | Bajo (BD relacional + backups) | **Eliminado** |
| Comparativo interanual | 1-2 horas (copiar/pegar entre hojas) | Automático con filtros | **~99%** |
| Tracking de metas por agente | Manual con calculadora | Dashboard en tiempo real | **Total** |
| Número de archivos Excel necesarios | 4-6 (>300 MB total) | 0 | **-100%** |

---

## 🎯 Priorización Recomendada

```
                    IMPACTO ALTO
                        ▲
                        │
    ╔═══════════════════╪════════════════════╗
    ║  FASE 1           │  FASE 0            ║
    ║  Dashboard        │  Datos Reales      ║
    ║  Ejecutivo        │  (Reporte Cubo)    ║
    ║                   │                    ║
 ───╬───────────────────┼────────────────────╬──▶ ESFUERZO
    ║  FASE 4           │  FASE 2            ║    BAJO
    ║  Proyecciones     │  Cobranza/         ║
    ║  Financieras      │  Deudor            ║
    ║                   │                    ║
    ║  FASE 5           │  FASE 3            ║
    ║  MIGGO Avanzado   │  Modelo Enriquecido║
    ╚═══════════════════╪════════════════════╝
                        │
                    IMPACTO BAJO
```

**Ruta crítica:** Fase 0 → Fase 1 → Fase 2 → (Fase 3 y 4 en paralelo) → Fase 5

---

## 📋 Checklist de Arranque Inmediato

- [ ] **Cargar `Reporte_Cubo_2025_ALL (3).xlsx`** a la BD (993 pólizas reales)
- [ ] **Extender el modelo de datos** con los 13 campos descubiertos
- [ ] **Actualizar `rules.py`** con los 6 estatus del catálogo real
- [ ] **Crear importador** para el formato del Reporte Cubo (3 hojas)
- [ ] **Replicar Vista Directiva** del `VISTAS.xlsx` como nuevo dashboard
- [ ] **Agregar dimensión Segmento** (ALFA/BETA/OMEGA) al dashboard

---

*Roadmap generado el 24 de febrero de 2026 a partir del análisis detallado de 7 archivos fuente.*  
*Sistema MAG v0.1.0 → Target v1.0*
