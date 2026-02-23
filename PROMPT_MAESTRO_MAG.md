# PROMPT MAESTRO – Sistema de Gestión de Producción para Promotoría de Seguros AXA

---

## INSTRUCCIÓN PRINCIPAL

Eres un ingeniero de software senior especializado en aplicaciones web para el sector asegurador mexicano. Tu tarea es diseñar y construir una **aplicación web completa** que reemplace un sistema basado en archivos Excel (de hasta 170 MB con 57 hojas) que actualmente utiliza una promotoría de seguros AXA para gestionar su producción de los ramos de **Vida Individual** y **Gastos Médicos Mayores (GMM) Individual**.

La aplicación debe:
1. **Extraer datos de PDFs** de pólizas de seguros mediante scraping/parsing
2. **Almacenar toda la información en una base de datos relacional** con esquema normalizado
3. **Aplicar automáticamente las reglas de negocio** para clasificar pólizas y calcular métricas
4. **Presentar un dashboard interactivo** con KPIs de desempeño y capacidades de filtrado multidimensional

---

## CONTEXTO DEL NEGOCIO

### ¿Qué es una promotoría de seguros?
Una promotoría es una organización que agrupa a múltiples agentes de seguros bajo la marca de una aseguradora (en este caso AXA). La promotoría se encarga de:
- Reclutar y gestionar agentes
- Dar seguimiento a la producción (pólizas vendidas y primas cobradas)
- Validar los indicadores oficiales que AXA calcula mensualmente
- Reportar resultados a la gerencia y al promotor titular

### Ramos que maneja
| Ramo | Productos principales | Métricas clave |
|------|----------------------|----------------|
| **Vida Individual** | Mi Proyecto R / Plan Personal de Retiro, Vida y Ahorro | Pólizas Equivalentes Primer Año, Prima Primer Año Vida |
| **GMM Individual** | Flex Plus (gamas: Zafiro, Diamante, Esmeralda, Rubí, etc.) | Asegurados Primer Año, Prima Primer Año GMM, Pólizas Primer Año |

### Estructura organizacional
```
Promotoría (MAG)
├── Promotor Titular
├── Gerencia(s)
│   ├── Oficina(s)
│   │   ├── Territorio(s)
│   │   │   ├── Agente 1 (código: 47968, CC: 56991)
│   │   │   ├── Agente 2 (código: 627523, CC: 606266)
│   │   │   └── ...
```

Cada agente tiene: código de agente, nombre completo, rol, situación (activo/cancelado/rehabilitado), fecha de alta, territorio, oficina, gerencia, promotor, nombre de promotoría, y centro de costos (CC).

---

## MÓDULO 1: EXTRACCIÓN DE DATOS (PDF SCRAPING)

### Fuente de Datos
Los PDFs de pólizas son documentos generados por el sistema AXA que contienen la información completa de cada póliza emitida. Actualmente se extraen y cargan a un Excel llamado `POLIZAS01`.

### Estructura de datos a extraer de cada PDF de póliza (56 campos)

```
CAMPOS DE IDENTIFICACIÓN:
- ID                    → Identificador interno único
- VERSION               → Versión del documento (generalmente 0)
- POLIZA                → Número de póliza (ej: "0076384A", "10007U00")
- ARCHIVO_PDF           → Nombre del archivo PDF fuente (ej: "0076384A.pdf")
- SOLICITUD             → Número de solicitud
- REGISTRO              → Clave de registro CNSF (ej: "CNSF-S0048-0440-2011")
- ENDOSO                → Número de endoso (si aplica)

CAMPOS DEL ASEGURADO/CONTRATANTE:
- ASEGURADO             → Nombre completo del asegurado (APELLIDOS, NOMBRE)
- CONTRATANTE           → Nombre del contratante (puede diferir del asegurado)
- RFC                   → RFC del contratante
- DOMCONTRA             → Domicilio del contratante
- CP                    → Código postal
- TEL                   → Teléfono de contacto
- EMAIL                 → Correo electrónico
- ASEGS                 → Número de asegurados en la póliza

CAMPOS DEL PRODUCTO:
- NOMRAMO               → Nombre del ramo: "VIDA" | "GASTOS MEDICOS MAYORES INDIVIDUAL"
- RAMO                  → Código de ramo: 11 (Vida) | 34 (GMM)
- PLAN                  → Plan del producto: "VIDA Y AHORRO", "FLEX PLUS", etc.
- GAMA                  → Gama del producto GMM: "ZAFIRO" | "DIAMANTE" | "ESMERALDA" | "RUBI" | etc.
- COBERTURA             → Descripción de la cobertura
- PLAZOPAGO             → Plazo de pago: "32 AÑOS", "100 años", etc.
- TOPE                  → Tope de cobertura (ej: "55000", "58000")
- ZONA                  → Zona geográfica: "Zona 1", "Zona 6", "Zona 11"

CAMPOS FINANCIEROS:
- PRIMA_TOT             → Prima total (incluye recargos e IVA)
- PRIMANETA             → Prima neta (sin recargos ni IVA)
- IVA                   → Monto de IVA
- RECARGO               → Monto de recargo por fraccionamiento
- DERECHO               → Derecho de póliza
- SUMA                  → Suma asegurada
- DEDUCIBLE             → Monto de deducible (en GMM)
- CESION                → Cesión (en GMM)
- COASEGURO             → Porcentaje de coaseguro (en GMM)
- MON                   → Moneda: "MN" | "USD" | "UDIS"
- INCSUM                → Incremento de suma asegurada
- PRIINCSUM             → Prima del incremento de suma asegurada
- PRIADI                → Prima adicional
- DESCFAM               → Descuento familiar

CAMPOS DE VIGENCIA:
- FECEMI                → Fecha de emisión
- FECINI                → Fecha de inicio de vigencia (CRÍTICA para clasificación)
- FECFIN                → Fecha de fin de vigencia
- FECIMPRE              → Fecha de impresión

CAMPOS DE COBRANZA Y PAGO:
- FP                    → Forma/Frecuencia de pago: "MENSUAL" | "ANUAL" | "TRIMESTRAL" | "SEMESTRAL"
- TIPPAG                → Tipo de pago: "CARGO AUTOMATICO" | "Tarjeta" | "Agente"
- STATUS                → Estado del recibo AXA: "PAGADA" | "CANC/X F.PAGO" | "CANC/X SUSTITUCION"
- MATERNIDAD            → Cobertura de maternidad (en GMM)

CAMPOS DE AGENTE:
- AGENTE                → Código del agente que vendió la póliza
- CC                    → Centro de costos del agente

CAMPOS DE CLASIFICACIÓN INTERNA:
- NUEVA                 → Flag calculado: 1 = póliza nueva, 0 = no nueva
- MYSTATUS              → Estado interno calculado: "CANCELADA NO TOMADA" | "CANCELADA CADUCADA" | "PAGADA TOTAL" | "TERMINADA" | "" (activa)
- MIGRADA               → Flag de migración
- REN                   → Número de renovación
- RED                   → Red hospitalaria: "ABIERTA"
- TABULADOR             → Tabulador (en GMM): "CEDRO" | "FRESNO" | "ROBLE"
- NOTA                  → Notas adicionales
- CONDICIONES           → URL a condiciones generales del producto
- PLASEG                → Plazo del seguro
```

### Normalización del Número de Póliza ("Póliza Estándar")
**IMPORTANTE:** El número de póliza puede aparecer en diferentes formatos según la fuente:
- Con ceros iniciales o sin ellos
- Con sufijo `-NNN` o sin él
- Con terminación `00` (original) o `NN+1` (reexpedida)

Se DEBE crear un campo `POLIZA_ESTANDAR` que normalice todas las variaciones para que los cruces funcionen correctamente. Algoritmo sugerido:
1. Eliminar ceros iniciales no significativos
2. Separar la parte base del sufijo de versión
3. Almacenar ambos: `POLIZA_ORIGINAL` y `POLIZA_ESTANDAR`

### Detección de Reexpediciones
- Pólizas nuevas se emiten con terminación `00`
- Si la póliza se modifica en los primeros 9 meses, se reexpide con terminación `01`, `02`, etc.
- Una póliza reexpedida sigue siendo "nueva" hasta 365 días después de su inicio de vigencia original
- Se debe crear una relación `póliza original ↔ póliza reexpedida` cuando se detecte

---

## MÓDULO 2: MODELO DE DATOS (BASE DE DATOS RELACIONAL)

### Esquema propuesto

```sql
-- ============================================================
-- CATÁLOGOS
-- ============================================================

CREATE TABLE agentes (
    id                  SERIAL PRIMARY KEY,
    codigo_agente       VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo     VARCHAR(200) NOT NULL,
    rol                 VARCHAR(50),
    situacion           VARCHAR(50) DEFAULT 'ACTIVO',  -- ACTIVO, CANCELADO, REHABILITADO
    fecha_alta          DATE,
    fecha_rehabilitacion DATE,
    fecha_cancelacion   DATE,
    causa_cancelacion   VARCHAR(200),
    territorio          VARCHAR(100),
    oficina             VARCHAR(100),
    gerencia            VARCHAR(100),
    promotor            VARCHAR(100),
    nombre_promotoria   VARCHAR(200),
    centro_costos       VARCHAR(20),
    telefono            VARCHAR(20),
    email               VARCHAR(200),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE productos (
    id                  SERIAL PRIMARY KEY,
    ramo_codigo         INTEGER NOT NULL,         -- 11 = Vida, 34 = GMM
    ramo_nombre         VARCHAR(100) NOT NULL,     -- "VIDA", "GASTOS MEDICOS MAYORES INDIVIDUAL"
    plan                VARCHAR(100),              -- "FLEX PLUS", "VIDA Y AHORRO"
    gama                VARCHAR(50),               -- "ZAFIRO", "DIAMANTE", etc.
    registro_cnsf       VARCHAR(50),               -- "CNSF-S0048-0327-2024"
    condiciones_url     TEXT,
    UNIQUE(ramo_codigo, plan, gama)
);

-- ============================================================
-- TABLA PRINCIPAL DE PÓLIZAS
-- ============================================================

CREATE TABLE polizas (
    id                  SERIAL PRIMARY KEY,
    
    -- Identificación
    poliza_original     VARCHAR(30) NOT NULL,      -- Número tal cual viene del PDF
    poliza_estandar     VARCHAR(30) NOT NULL,      -- Número normalizado para cruces
    version             INTEGER DEFAULT 0,
    solicitud           VARCHAR(30),
    archivo_pdf         VARCHAR(200),              -- Nombre del PDF fuente
    endoso              VARCHAR(20),
    
    -- Relaciones
    agente_id           INTEGER REFERENCES agentes(id),
    producto_id         INTEGER REFERENCES productos(id),
    
    -- Asegurado / Contratante
    asegurado_nombre    VARCHAR(200),
    contratante_nombre  VARCHAR(200),
    rfc                 VARCHAR(20),
    domicilio           TEXT,
    codigo_postal       VARCHAR(10),
    telefono            VARCHAR(20),
    email               VARCHAR(200),
    num_asegurados      INTEGER DEFAULT 1,
    
    -- Vigencia
    fecha_emision       DATE,
    fecha_inicio        DATE NOT NULL,             -- FECINI: CRÍTICA para clasificación
    fecha_fin           DATE,
    fecha_impresion     DATE,
    
    -- Financieros
    moneda              VARCHAR(5) DEFAULT 'MN',   -- MN, USD, UDIS
    prima_total         DECIMAL(14,2),
    prima_neta          DECIMAL(14,2),
    iva                 DECIMAL(14,2),
    recargo             DECIMAL(14,2),
    derecho_poliza      DECIMAL(14,2),
    suma_asegurada      DECIMAL(16,2),
    deducible           DECIMAL(14,2),
    cesion              DECIMAL(14,2),
    coaseguro           DECIMAL(5,2),
    incremento_suma     DECIMAL(14,2),
    prima_incremento    DECIMAL(14,2),
    prima_adicional     DECIMAL(14,2),
    descuento_familiar  DECIMAL(14,2),
    
    -- Cobranza
    forma_pago          VARCHAR(20),               -- MENSUAL, ANUAL, TRIMESTRAL, SEMESTRAL
    tipo_pago           VARCHAR(30),               -- CARGO AUTOMATICO, Tarjeta, Agente
    status_recibo       VARCHAR(50),               -- PAGADA, CANC/X F.PAGO, CANC/X SUSTITUCION
    
    -- Producto específico
    plazo_pago          VARCHAR(30),
    tope                DECIMAL(14,2),
    zona                VARCHAR(20),
    red                 VARCHAR(30),               -- ABIERTA
    tabulador           VARCHAR(30),               -- CEDRO, FRESNO, ROBLE
    maternidad          VARCHAR(20),
    cobertura           TEXT,
    
    -- Clasificación calculada (se llena automáticamente por reglas de negocio)
    es_nueva            BOOLEAN,                   -- Resultado de la clasificación
    tipo_poliza         VARCHAR(20),               -- NUEVA, SUBSECUENTE, NO_APLICA
    tipo_prima          VARCHAR(20),               -- BASICA, EXCEDENTE (solo Vida)
    pct_comision        DECIMAL(8,4),              -- % Comisión calculado (solo Vida)
    poliza_padre_id     INTEGER REFERENCES polizas(id), -- Para reexpediciones
    es_reexpedicion     BOOLEAN DEFAULT FALSE,
    mystatus            VARCHAR(50),               -- Estado interno calculado
    
    -- Metadata
    periodo_aplicacion  VARCHAR(7),                -- "2026-01" (año-mes del periodo donde aplica)
    anio_aplicacion     INTEGER,                   -- Año fiscal donde aplica
    trimestre_aplicacion INTEGER,                   -- 1, 2, 3, 4
    
    -- Auditoría
    fecha_importacion   TIMESTAMPTZ DEFAULT NOW(),
    fuente              VARCHAR(50) DEFAULT 'PDF', -- PDF, EXCEL_IMPORT, MANUAL
    notas               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Índices críticos para performance
CREATE INDEX idx_polizas_estandar ON polizas(poliza_estandar);
CREATE INDEX idx_polizas_agente ON polizas(agente_id);
CREATE INDEX idx_polizas_fecha_inicio ON polizas(fecha_inicio);
CREATE INDEX idx_polizas_tipo ON polizas(tipo_poliza);
CREATE INDEX idx_polizas_periodo ON polizas(periodo_aplicacion);
CREATE INDEX idx_polizas_anio ON polizas(anio_aplicacion);

-- ============================================================
-- INDICADORES AXA (datos oficiales recibidos mensualmente)
-- ============================================================

CREATE TABLE indicadores_axa (
    id                  SERIAL PRIMARY KEY,
    periodo             VARCHAR(7) NOT NULL,       -- "2025-07" (año-mes)
    fecha_recepcion     DATE,
    
    -- Identificación
    poliza              VARCHAR(30),
    agente_codigo       VARCHAR(20),
    
    -- Métricas AXA
    ramo                VARCHAR(100),
    num_asegurados      INTEGER,
    polizas_equivalentes DECIMAL(10,4),
    prima_primer_anio   DECIMAL(14,2),
    prima_subsecuente   DECIMAL(14,2),
    antiguedad_axa      DATE,                      -- Antigüedad AXA Individual
    fecha_inicio_vigencia DATE,
    es_nueva_axa        BOOLEAN,                   -- Si AXA la clasifica como nueva
    reconocimiento_antiguedad BOOLEAN,             -- Si tiene reconocimiento previo
    
    -- Para conciliación
    encontrada_en_base  BOOLEAN,
    diferencia_clasificacion TEXT,                  -- Descripción de diferencia si existe
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_indicadores_periodo ON indicadores_axa(periodo);
CREATE INDEX idx_indicadores_poliza ON indicadores_axa(poliza);

-- ============================================================
-- CONCILIACIÓN (resultado del cruce)
-- ============================================================

CREATE TABLE conciliaciones (
    id                  SERIAL PRIMARY KEY,
    periodo             VARCHAR(7) NOT NULL,
    fecha_conciliacion  TIMESTAMPTZ DEFAULT NOW(),
    
    poliza_id           INTEGER REFERENCES polizas(id),
    indicador_axa_id    INTEGER REFERENCES indicadores_axa(id),
    
    -- Resultado
    status              VARCHAR(30),               -- COINCIDE, DIFERENCIA, SOLO_INTERNO, SOLO_AXA
    tipo_diferencia     TEXT,                       -- Descripción de la diferencia
    
    -- Valores comparados
    clasificacion_interna VARCHAR(20),
    clasificacion_axa   VARCHAR(20),
    prima_interna       DECIMAL(14,2),
    prima_axa           DECIMAL(14,2),
    
    resuelto            BOOLEAN DEFAULT FALSE,
    notas_resolucion    TEXT,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- METAS Y PRESUPUESTOS
-- ============================================================

CREATE TABLE metas (
    id                  SERIAL PRIMARY KEY,
    anio                INTEGER NOT NULL,
    periodo             VARCHAR(7),                -- NULL = meta anual, "2025-01" = meta mensual
    agente_id           INTEGER REFERENCES agentes(id), -- NULL = meta de la promotoría
    
    -- Metas por ramo
    meta_polizas_vida   INTEGER,
    meta_prima_vida     DECIMAL(14,2),
    meta_polizas_gmm    INTEGER,
    meta_asegurados_gmm INTEGER,
    meta_prima_gmm      DECIMAL(14,2),
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LOG DE IMPORTACIONES
-- ============================================================

CREATE TABLE importaciones (
    id                  SERIAL PRIMARY KEY,
    tipo                VARCHAR(20) NOT NULL,       -- PDF, INDICADORES_AXA, EXCEL_HISTORICO
    archivo_nombre      VARCHAR(200),
    registros_procesados INTEGER,
    registros_nuevos    INTEGER,
    registros_actualizados INTEGER,
    registros_error     INTEGER,
    errores_detalle     JSONB,
    usuario             VARCHAR(100),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## MÓDULO 3: REGLAS DE NEGOCIO (MOTOR DE CLASIFICACIÓN)

### El motor de clasificación debe ejecutarse automáticamente cada vez que se importan pólizas nuevas o se actualiza la información.

### REGLA 1: Clasificación Nueva vs. Subsecuente

```
PARA CADA PÓLIZA:

SI ramo = "GMM":
    SI año(FECINI) = año_periodo_analisis 
       Y STATUS = "PAGADA" 
       Y el recibo aplicado coincide con FECINI:
        → tipo_poliza = "NUEVA"
    SI año(FECINI) = año_periodo_analisis - 1
       Y tiene pagos aplicados en año_periodo_analisis:
        → tipo_poliza = "SUBSECUENTE"
    SINO:
        → tipo_poliza = "NO_APLICA"

SI ramo = "VIDA":
    CALCULAR pct_comision = comision / prima_neta
    SI pct_comision >= 0.021:
        → tipo_prima = "BASICA"    (computa al promotor ✅)
    SINO:
        → tipo_prima = "EXCEDENTE" (NO computa ❌)
    
    SI tipo_prima = "BASICA":
        SI año(FECINI) = año_periodo_analisis:
            → tipo_poliza = "NUEVA"
        SI año(FECINI) = año_periodo_analisis - 1
           Y tiene pagos en año_periodo_analisis:
            → tipo_poliza = "SUBSECUENTE"
        SINO:
            → tipo_poliza = "NO_APLICA"
    SINO:
        → tipo_poliza = "NO_APLICA" (prima excedente no computa)
```

### REGLA 2: Validación de Asegurado Nuevo (GMM)

```
UN ASEGURADO ES "NUEVO" SI Y SOLO SI:
    1. Ha sido PAGADO en el periodo de análisis
    2. NO trae reconocimiento de antigüedad AXA Individual
    3. La antigüedad AXA Individual = fecha de inicio de vigencia de la póliza
    
SI antiguedad_axa != fecha_inicio_vigencia:
    → El asegurado tiene reconocimiento previo → NO es nuevo
```

### REGLA 3: Pólizas Equivalentes (Vida Individual)

```
PARA CONVERTIR A PÓLIZAS EQUIVALENTES:
    1. Obtener la prima de la póliza en la moneda original
    2. Convertir a Moneda Nacional (MN) usando tipo de cambio del periodo
    3. Aplicar los factores de equivalencia de AXA
    
NOTA: Los tipos de cambio y factores de equivalencia deben ser configurables
```

### REGLA 4: Frontera de Año (enero)

```
ALERTA AUTOMÁTICA:
    SI fecha_pago ENTRE enero 2 Y enero 5 del año_periodo_analisis:
        → MARCAR para revisión manual
        → NOTA: "Pago puede pertenecer al año anterior (T-1)"
```

### REGLA 5: Detección de Reexpediciones

```
PARA CADA PÓLIZA NUEVA (terminación "00"):
    BUSCAR en la base si existe una póliza con:
        - Misma raíz de número de póliza
        - Terminación > "00" (es decir, "01", "02", etc.)
        - Emitida dentro de los primeros 9 meses de vigencia
    
    SI se encuentra:
        → VINCULAR como reexpedición (poliza_padre_id)
        → La póliza sigue siendo "nueva" hasta 365 días post-FECINI original
```

### REGLA 6: Status Interno (MYSTATUS)

```
DETERMINAR MYSTATUS basado en STATUS del recibo y otras señales:
    SI STATUS = "CANC/X F.PAGO":
        → MYSTATUS = "CANCELADA CADUCADA"
    SI STATUS = "CANC/X SUSTITUCION":
        → MYSTATUS = "CANCELADA NO TOMADA"  
    SI STATUS = "PAGADA" Y póliza vigente:
        → MYSTATUS = "PAGADA TOTAL" o "TERMINADA" según corresponda
    
    NOTA: Las pólizas canceldas/caducadas/no tomadas deben cruzarse con
    el deudor por primas del sistema MIT para validar
```

---

## MÓDULO 4: CONCILIACIÓN AUTOMÁTICA VS. INDICADORES AXA

### Proceso de Conciliación

```
1. IMPORTAR indicadores AXA (Excel recibido mensualmente con hojas "Detalle" y "detalle_pol")
2. NORMALIZAR números de póliza de AXA al formato "Póliza Estándar"
3. CRUZAR cada póliza de indicadores AXA contra la base interna:
   
   PARA CADA PÓLIZA EN indicadores_axa:
       BUSCAR en polizas WHERE poliza_estandar = normalizar(poliza_axa)
       
       SI se encuentra:
           COMPARAR:
             - ¿Clasificación nueva/subsecuente coincide?
             - ¿Prima coincide?
             - ¿Número de asegurados coincide?
             - ¿Tiene reconocimiento de antigüedad cuando no debería?
           
           SI hay diferencia:
               → status = "DIFERENCIA"
               → Registrar tipo_diferencia con detalle
           SINO:
               → status = "COINCIDE"
       
       SI NO se encuentra:
           → status = "SOLO_AXA" (AXA la tiene pero nosotros no)
   
   PARA CADA PÓLIZA EN base_interna que NO está en indicadores_axa:
       → status = "SOLO_INTERNO" (nosotros la tenemos pero AXA no la reporta)

4. GENERAR reporte de diferencias con detalle y resumen
```

---

## MÓDULO 5: DASHBOARD DE KPIs

### 5.1 Filtros Globales (aplicables a todas las vistas)

- **Periodo:** Rango de fechas o selección de mes/trimestre/año
- **Ramo:** Vida Individual | GMM Individual | Todos
- **Agente:** Selección individual o múltiple por código o nombre
- **Territorio / Oficina / Gerencia:** Jerarquía organizacional
- **Centro de Costos (CC)**
- **Producto / Plan / Gama**
- **Tipo de póliza:** Nueva | Subsecuente | Todas
- **Status:** Pagada | Cancelada | Todas
- **Moneda**

### 5.2 Vista Principal: Resumen Ejecutivo

**KPIs en tarjetas prominentes:**

| KPI | Descripción | Desglose |
|-----|-------------|----------|
| **Pólizas Nuevas Vida** | Total de pólizas equivalentes primer año | vs. meta, % cumplimiento |
| **Prima Primer Año Vida** | Suma de prima básica de pólizas nuevas Vida | MN, vs. periodo anterior |
| **Pólizas Nuevas GMM** | Total pólizas primer año GMM | vs. meta, % cumplimiento |
| **Asegurados Nuevos GMM** | Total asegurados primer año GMM | vs. meta |
| **Prima Primer Año GMM** | Suma prima de pólizas nuevas GMM | MN, vs. periodo anterior |
| **Prima Subsecuente** | Prima T-1 pagada en periodo actual (ambos ramos) | por ramo |
| **Prima Total del Ejercicio** | Prima Nueva + Prima Subsecuente | por ramo |
| **Tasa de Persistencia** | % pólizas que siguen pagando vs. total emitidas | por ramo |
| **Pólizas Canceladas** | Total canceladas por tipo (falta pago, sustitución, no tomada) | por tipo |

**Gráficos:**
- 📊 **Barras:** Producción mensual (pólizas y prima) con línea de tendencia
- 📈 **Líneas:** Evolución de KPIs por mes/trimestre (comparativo año actual vs. anterior)
- 🍩 **Donas:** Distribución por ramo, por gama (GMM), por producto (Vida)
- 📊 **Barras horizontales:** Ranking de agentes por producción (Top 10 / Bottom 10)

### 5.3 Vista por Agente

**Tarjetas individuales por agente con:**
- Nombre, código, CC, territorio, oficina, gerencia
- KPIs personales: pólizas nuevas, prima, asegurados, % cumplimiento de meta
- Comparativo vs. promedio de la promotoría
- Gráfico de producción mensual del agente
- Listado de pólizas del agente con status y clasificación

### 5.4 Vista de Conciliación

**Panel dividido:**
- Izquierda: Resumen de conciliación (coincide / diferencia / solo AXA / solo interno)
- Derecha: Detalle de cada diferencia con campos comparados
- Indicadores: % de coincidencia, monto total de diferencia en prima
- Exportar reporte de diferencias a Excel/PDF

### 5.5 Vista de Detalle de Pólizas

**Tabla interactiva con:**
- Todas las pólizas con sus campos principales
- Ordenamiento por cualquier columna
- Filtros inline por columna
- Búsqueda global
- Indicadores visuales: 🟢 pagada, 🔴 cancelada, 🟡 pendiente
- Columna de clasificación (Nueva/Subsecuente) con el cálculo visible
- Exportar a Excel/CSV

### 5.6 Vista de Producción Histórica

**Gráficos de tendencia:**
- Producción anual comparativa (2022 vs. 2023 vs. 2024 vs. 2025 vs. 2026)
- Producción acumulada mes a mes (curva de acumulación)
- Heatmap de producción por agente × mes
- Proyecciones basadas en tendencia actual

### 5.7 Vista de Cartera

**Seguimiento de cartera vigente:**
- Pólizas próximas a vencer (30, 60, 90 días)
- Pólizas con pagos pendientes
- Pólizas en riesgo de cancelación por falta de pago
- Recordatorios automáticos

---

## MÓDULO 6: IMPORTACIÓN Y CARGA DE DATOS

### 6.1 Importación de PDFs de Pólizas
- Interfaz para subir uno o múltiples PDFs
- Procesamiento automático con extracción de campos
- Pantalla de revisión: campos extraídos vs. valores detectados
- Opción de corrección manual antes de guardar
- Log de importación con conteo de éxitos/errores

### 6.2 Importación de Indicadores AXA
- Subir el Excel de indicadores recibido de AXA
- Seleccionar las hojas "Detalle" y "detalle_pol"
- Mapeo automático de columnas
- Ejecutar conciliación automática tras importar

### 6.3 Importación Inicial (Datos Históricos)
- Carga masiva desde los Excel existentes (POLIZAS01, Base Histórica)
- Mapeo de columnas Excel → campos de la base de datos
- Validación y limpieza automática
- Reporte de registros importados/omitidos/con error

### 6.4 Gestión del Directorio de Agentes
- CRUD de agentes
- Importación masiva desde Excel
- Histórico de cambios de situación (alta, baja, rehabilitación)

---

## ESPECIFICACIONES TÉCNICAS

### Stack Tecnológico Recomendado
- **Frontend:** React/Next.js con dashboard library (Recharts, Tremor, o similar)
- **Backend:** API REST (Node.js/Python)
- **Base de Datos:** PostgreSQL (producción) o SQLite (MVP inicial)
- **PDF Parsing:** PyPDF2, pdfplumber, o Camelot (para tablas en PDFs)
- **Autenticación:** Simple con roles (Admin, Analista, Vista)

### Roles de Usuario
| Rol | Permisos |
|-----|----------|
| **Admin** | Todo: importar, editar, configurar, ver |
| **Analista** | Importar PDFs, ejecutar conciliación, editar clasificaciones, ver dashboard |
| **Vista** | Solo consultar dashboard y reportes |

### Requisitos No Funcionales
- Responsive (escritorio y tablet)
- Exportación a Excel y PDF desde cualquier vista
- Rendimiento: cargar dashboard con 10,000+ pólizas en < 3 segundos
- Backup automático de la base de datos
- Logs de auditoría de todas las operaciones

---

## DATOS DE EJEMPLO

### Póliza de Vida Individual
```json
{
    "poliza_original": "0076384A",
    "poliza_estandar": "76384A",
    "agente_codigo": "47968",
    "asegurado": "SALAZAR CASTILLO, JUAN FRANCISCO",
    "ramo": "VIDA",
    "plan": "VIDA Y AHORRO",
    "cobertura": "MI PROYECTO R / PLAN PERSONAL DE RETIRO",
    "fecha_inicio": "2024-08-08",
    "fecha_fin": "2056-08-08",
    "forma_pago": "MENSUAL",
    "tipo_pago": "CARGO AUTOMATICO",
    "moneda": "MN",
    "prima_total": 28077.00,
    "prima_neta": 28077.00,
    "suma_asegurada": 1000000.00,
    "registro_cnsf": "CNSF-S0048-0440-2011",
    "status_recibo": "PAGADA"
}
```

### Póliza de GMM
```json
{
    "poliza_original": "10007U00",
    "poliza_estandar": "10007U00",
    "agente_codigo": "627523",
    "asegurado": "CARRASCO RIVERA, VERENICE",
    "ramo": "GASTOS MEDICOS MAYORES INDIVIDUAL",
    "plan": "FLEX PLUS",
    "gama": "ZAFIRO",
    "fecha_inicio": "2024-09-25",
    "fecha_fin": "2025-09-25",
    "forma_pago": "MENSUAL",
    "tipo_pago": "Tarjeta",
    "moneda": "MN",
    "prima_total": 24568.10,
    "prima_neta": 17916.88,
    "iva": 3388.70,
    "recargo": 1612.52,
    "suma_asegurada": 31500000.00,
    "deducible": 50000,
    "coaseguro": 10,
    "red": "ABIERTA",
    "tabulador": "CEDRO",
    "tope": 55000,
    "zona": "Zona 1",
    "registro_cnsf": "CNSF-S0048-0327-2024",
    "status_recibo": "PAGADA",
    "num_asegurados": 1,
    "maternidad": "16000.00"
}
```

---

## ENTREGABLES ESPERADOS

1. **Base de datos** con esquema completo y datos de ejemplo
2. **API/Backend** con endpoints para:
   - CRUD de pólizas, agentes, productos
   - Importación de PDFs con extracción automática
   - Importación de indicadores AXA
   - Motor de clasificación automática
   - Conciliación automática
   - Consultas filtradas para dashboard
3. **Frontend/Dashboard** con:
   - Las 7 vistas descritas en el Módulo 5
   - Filtros interactivos
   - Exportación a Excel/PDF
   - Diseño moderno, responsive
4. **Documentación** de reglas de negocio implementadas

---

## NOTAS PARA LA IA

- **Prioriza la correcta implementación de las reglas de negocio** sobre la estética. Las clasificaciones Nueva/Subsecuente y Básica/Excedente son la razón de ser del sistema.
- Los volúmenes actuales son ~10,000 pólizas totales, ~450 Vida y ~2,700 GMM. No se necesita arquitectura para millones de registros.
- El dashboard reemplaza a un Excel de 57 hojas y 103 MB. Cada hoja del Excel original representa una "vista" o "reporte" que ahora debe ser un filtro o vista en el dashboard.
- Los datos de agentes incluyen jerarquía: Promotoría → Gerencia → Oficina → Territorio → Agente.
- AXA envía indicadores mensualmente (a mes vencido). La conciliación es el proceso más crítico y que más tiempo consume actualmente.
- El % de comisión de 2.1% para clasificar prima básica vs. excedente es un umbral de negocio que puede cambiar. Debe ser configurable.

---

*Prompt generado el 23 de febrero de 2026 basado en el análisis de los archivos operativos de la promotoría MAG.*
