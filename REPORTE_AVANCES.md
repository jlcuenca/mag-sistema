# 📊 Reporte de Avances — Sistema MAG
**Promotoría de Seguros AXA — Ramos Vida Individual y GMM Individual**

**Fecha:** 23 de febrero de 2026  
**Estado general:** 🟢 MVP funcional corriendo en producción local

---

## ✅ Sesión del 23 de Febrero 2026

### 1. Análisis y Documentación (Completado)

- **`ANALISIS_MAG.md`** — Análisis completo de los 6 archivos operativos de la promotoría:
  - Inventario de archivos (procedimientos, bases Excel, oferta de valor)
  - Flujos de negocio documentados (clasificación pólizas, conciliación AXA)
  - 6 problemas identificados + 6 oportunidades de automatización
  - Diagrama ASCII del proceso de negocio completo

- **`PROMPT_MAESTRO_MAG.md`** — Especificación técnica completa del sistema a construir:
  - 6 módulos definidos (PDF scraping, BD, reglas negocio, conciliación, dashboard, importación)
  - Esquema SQL completo (7 tablas)
  - 6 reglas de negocio documentadas
  - Stack tecnológico: Next.js + SQLite + Recharts

---

### 2. Infraestructura (Completado)

| Componente | Versión | Estado |
|------------|---------|--------|
| Node.js LTS | v24.13.1 | ✅ Instalado vía winget |
| npm | v11.8.0 | ✅ Funcionando |
| Next.js | v16.1.6 | ✅ App creada en `/sistema` |
| better-sqlite3 | última | ✅ Base de datos local |
| Recharts | última | ✅ Gráficas interactivas |
| lucide-react | última | ✅ Iconos |
| xlsx | última | ✅ Para exportación |

**URL local:** `http://localhost:3000`  
**Directorio del proyecto:** `c:\Users\jlcue\Documents\mag\sistema\`

---

### 3. Aplicación Web Construida (MVP Completo)

#### Estructura de archivos creados:

```
sistema/
├── next.config.mjs              ✅ Config Turbopack + SQLite
├── lib/
│   ├── db.js                    ✅ Base de datos SQLite + seed de datos
│   └── rules.js                 ✅ Motor de reglas de negocio
├── components/
│   └── Sidebar.js               ✅ Navegación lateral
├── app/
│   ├── globals.css              ✅ Diseño dark premium completo
│   ├── layout.js                ✅ Layout raíz
│   ├── page.js                  ✅ Redirección a dashboard
│   ├── dashboard/page.js        ✅ Dashboard principal
│   ├── polizas/page.js          ✅ Tabla de pólizas con filtros
│   ├── agentes/page.js          ✅ Directorio de agentes en cards
│   ├── conciliacion/page.js     ✅ Conciliación vs. AXA
│   ├── produccion/page.js       ✅ Histórico 2022–2026
│   ├── cartera/page.js          ✅ Alertas de vencimiento
│   └── api/
│       ├── dashboard/route.js   ✅ API KPIs y gráficas
│       ├── polizas/route.js     ✅ API CRUD pólizas
│       ├── agentes/route.js     ✅ API directorio agentes
│       └── conciliacion/route.js ✅ API conciliación automática
```

---

### 4. Base de Datos SQLite Inicializada

**Archivo:** `sistema/data/mag.db`

| Tabla | Registros iniciales | Descripción |
|-------|--------------------|-|
| `agentes` | 8 | Directorio de agentes (7 activos, 1 cancelado) |
| `productos` | 6 | Catálogo de planes Vida y GMM |
| `polizas` | 110 | 30 Vida + 80 GMM (datos de ejemplo) |
| `indicadores_axa` | 4 | Indicadores julio 2025 para conciliación |
| `metas` | 13 | Metas mensuales y anuales 2025 |
| `conciliaciones` | 0 | Vacío (se llena automáticamente) |
| `importaciones` | 0 | Log de importaciones |

---

### 5. Módulos Funcionales

#### 📊 Dashboard de Producción
- **8 KPI cards** con barra de progreso vs. meta:
  - Pólizas Nuevas Vida / Prima Nueva Vida
  - Pólizas Nuevas GMM / Asegurados Nuevos GMM / Prima Nueva GMM
  - Prima Subsecuente Vida y GMM
  - Pólizas Canceladas
- **Gráfica de barras:** Producción mensual Vida vs GMM (por año)
- **Gráfica de dona:** Distribución GMM por Gama (Zafiro, Diamante, Esmeralda, Rubí)
- **Gráfica de líneas:** Prima nueva por mes Vida vs GMM
- **Tabla Top 10 Agentes** con ranking y barra de participación
- **Selector de año** (2022–2026)

#### 📋 Pólizas
- Tabla con 56 campos principales
- Filtros por: ramo (Vida/GMM), tipo (Nueva/Subsecuente/No aplica), año
- Búsqueda por número de póliza o nombre de asegurado
- Paginación (50 por página)
- Indicadores visuales: pills de status y tipo

#### 👥 Agentes
- Grid de cards individuales
- Info: código, rol, situación, territorio, oficina, gerencia, CC
- KPIs por agente: total pólizas, nuevas 2025, prima 2025
- Filtro por situación (Activo / Cancelado / Todos)

#### 🔄 Conciliación AXA
- Cruce automático indicadores AXA vs. base interna
- Estados: Coincide ✅ / Diferencia ⚠️ / Solo AXA ❌ / Solo Interno 🔵
- Gráfica de dona con distribución de resultado
- % de coincidencia global
- Detalle por póliza con tipo de diferencia
- Selector de periodo (mes-año)

#### 📈 Producción Histórica
- Comparativo anual 2022–2026 en barras
- Curva mensual multi-año (líneas por año)
- Toggle Pólizas / Prima

#### 💼 Cartera
- Alertas de vencimiento en 30 / 60 / 90 días
- Listado de pólizas canceladas por falta de pago
- Código de colores: 🔴 ≤30d / 🟡 ≤60d / 🔵 ≤90d

---

### 6. Reglas de Negocio Implementadas

| Regla | Descripción | Estado |
|-------|-------------|--------|
| **R1** | Clasificación Nueva vs. Subsecuente (GMM y Vida) | ✅ |
| **R2** | Prima Básica vs. Excedente (umbral 2.1% comisión) | ✅ |
| **R3** | Validación asegurado nuevo GMM (antigüedad AXA) | ✅ |
| **R4** | Alerta frontera de año (pagos 2–5 enero) | ✅ |
| **R5** | Detección de reexpediciones (terminación NN+1) | ✅ |
| **R6** | MYSTATUS calculado (Cancelada Caducada / No Tomada) | ✅ |
| **R7** | Normalización número de póliza (Póliza Estándar) | ✅ |

---

## 🔲 Pendiente — Próximas Iteraciones

### Alta prioridad
- [ ] **Importación de Excel** — Cargar `POLIZAS01_19022026.xlsx` real a la BD
- [ ] **Importación de indicadores AXA** — Subir Excel de AXA y ejecutar conciliación
- [ ] **Parser de PDF de pólizas** — Extracción automática de los 56 campos
- [ ] **Exportación a Excel/CSV** — Desde cualquier vista del dashboard

### Media prioridad
- [ ] **Autenticación** — Roles Admin / Analista / Vista
- [ ] **Configuración del umbral 2.1%** — Panel de configuración
- [ ] **Tipos de cambio USD/UDIS** — Para pólizas Equivalentes
- [ ] **Metas por agente** — KPIs individuales vs. meta

### Baja prioridad
- [ ] **Notificaciones/alertas** — Email/WhatsApp para vencimientos
- [ ] **Backup automático** — Respaldo programado de la BD
- [ ] **PWA / responsive móvil** — Adaptación tablet/celular

---

## 🚀 Cómo arrancar el sistema

```powershell
# En PowerShell (nueva terminal):
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
cd C:\Users\jlcue\Documents\mag\sistema
npm run dev
```

Luego abrir en el browser: **http://localhost:3000**

---

*Reporte generado automáticamente el 23 de febrero de 2026 — Sistema MAG v0.1.0 MVP*
