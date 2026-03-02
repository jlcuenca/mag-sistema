# 📋 Reporte de Avances — MAG Sistema
## Promotoría MAG · AXA Seguros México

---

## 📅 Reporte del 2 de Marzo, 2026

### 👥 Participantes
- **JL Cuenca** — Dirección técnica y validación de negocio
- **Antigravity AI** — Desarrollo e implementación

---

## ✅ Logros del Día

### 1. 🗃️ Reimportación Completa de Base de Datos
**Estado**: ✅ Completado y verificado

Se ejecutó una reimportación limpia de toda la base de datos desde el archivo fuente `POLIZAS_01_08022026.xlsx`:

| Métrica | Valor |
|---|---|
| Pólizas importadas | **9,997** |
| Agentes creados | **197** |
| Productos creados | **11** |
| Ramo Automóviles | 6,920 pólizas |
| Ramo GMM | 2,638 pólizas |
| Ramo Vida | 439 pólizas |
| Pólizas pagadas (flag_pagada) | 6,604 |

**Archivos creados**:
- `scripts/reimportar_polizas.py` — Script de reimportación completa con recreación de tablas, catálogos, e importación
- `scripts/verificar_bd.py` — Script de verificación post-importación
- `scripts/test_api.py` — Script de pruebas de endpoints API

**Mejora al motor de reglas**: Se amplió la lógica de `aplicar_reglas_poliza()` en `api/rules.py` para reconocer estatus pagados del Excel (`PAGADA TOTAL`, `TERMINADA PAGADA`, `PAGADA S/FP`, `ANTICIPADA`) como indicadores de pago, mejorando significativamente la precisión del cálculo `flag_pagada`.

---

### 2. 📄 Visor de Documentos PDF
**Estado**: ✅ Completado y desplegado

Se implementó la funcionalidad de visualización de documentos PDF directamente desde la aplicación, conectando al servidor de documentos de AXA.

**URLs configuradas**:
- **Pólizas**: `http://54.184.22.19:7070/cartera-0.1/static/archivos/{num_poliza}.pdf`
- **Solicitudes**: `http://54.184.22.19:7070/cartera-0.1/static/archivos/solicitudes/{num_solicitud}.pdf`

**Funcionalidades entregadas**:

| Feature | Pólizas | Solicitudes |
|---|---|---|
| Botón 📄 en tabla | ✅ Columna "Doc" | ✅ Columna "Doc" |
| Botón en vista Kanban | N/A | ✅ "📄 Ver Doc" |
| Modal visor PDF | ✅ Glassmorphism + slideUp | ✅ Glassmorphism + slideUp |
| Abrir en nueva pestaña | ✅ | ✅ |
| Descargar PDF | ✅ | ✅ |
| Info en header (nombre, asegurado) | ✅ | ✅ |

**Archivos modificados**:
- `sistema/lib/api.js` — Funciones `getPolizaDocUrl()` y `getSolicitudDocUrl()`
- `sistema/app/polizas/page.js` — Columna Doc + modal visor
- `sistema/app/solicitudes/page.js` — Botón Doc en Kanban/tabla + modal visor
- `sistema/app/globals.css` — Animación `@keyframes slideUp`

**Parámetro configurable**: `doc_url_base` en tabla `configuracion` de la BD, editable desde la UI de Configuración del sistema.

---

### 3. 🔒 Fix Mixed Content HTTPS
**Estado**: ✅ Completado y desplegado

**Problema detectado**: Al abrir PDFs desde la versión producción (`https://mag-sistema.vercel.app`), el navegador bloqueaba la carga del iframe por Mixed Content (HTTPS → HTTP).

**Solución implementada**: Proxy PDF en el backend FastAPI.

```
Frontend (HTTPS/Vercel) → Backend Proxy (HTTPS/Render) → Servidor PDF (HTTP/54.184.22.19)
```

| Componente | Cambio |
|---|---|
| `api/routers.py` | Nuevo `router_documentos` con endpoints `/documentos/poliza/{num}` y `/documentos/solicitud/{num}` |
| `main.py` | Registro del nuevo router |
| `requirements.txt` | Agregado `httpx==0.28.1` |
| `sistema/lib/api.js` | URLs apuntan al proxy backend |
| `sistema/vercel.json` | `X-Frame-Options` cambiado de `DENY` a `SAMEORIGIN` |

**Características del proxy**:
- Cache HTTP de 1 hora (`Cache-Control: public, max-age=3600`)
- Validación de entrada (solo caracteres alfanuméricos)
- URL base configurable desde tabla `configuracion`
- Manejo de errores: 404 (no encontrado), 504 (timeout), 502 (sin conexión)

---

### 4. 🗺️ Roadmap de Producto
**Estado**: ✅ Documento creado

Se analizaron **17 archivos de referencia** en la carpeta `/ref` para identificar funcionalidades pendientes y oportunidades de mejora. Se generó el documento `ROADMAP.md` con 6 fases priorizadas.

**Hallazgos principales**:
| Descubrimiento | Archivo | Registros |
|---|---|---|
| Historial completo de pagos | `PAGTOTAL_08022026.xlsx` | 160,822 |
| Pipeline solicitudes AXA | `Concentrado2026-02-27.csv` | 232 |
| Tracking de etapas | `Concentrado_UltEtapas.xlsx` | 3,937 |
| Fórmulas KPIs ejecutivos | `Paso a Paso Resultados.docx` | 3 tablas |
| Tabla Beta Productivo | `WhatsApp Image.jpeg` | Imagen |

---

## 📊 Deploys Realizados

| # | Commit | Descripción | Vercel | Render |
|---|---|---|---|---|
| 1 | `4b962a9` | feat: visor PDF + reimportación + reglas | ✅ Ready | ✅ Live |
| 2 | `8fd6802` | fix: X-Frame-Options SAMEORIGIN | ✅ Ready | ✅ Live |
| 3 | `632496b` | fix: proxy PDF Mixed Content | ✅ Ready | ✅ Live |

**URLs de producción**:
- Frontend: https://mag-sistema.vercel.app
- Backend API: https://mag-sistema.onrender.com
- Documentación API: https://mag-sistema.onrender.com/docs

---

## 📈 Estadísticas del Día

| Métrica | Valor |
|---|---|
| Commits realizados | **3** |
| Archivos creados | **6** (`reimportar_polizas.py`, `verificar_bd.py`, `test_api.py`, `ROADMAP.md`, `DIAGRAMA_FLUJO.html`, este reporte) |
| Archivos modificados | **9** |
| Líneas de código agregadas | **~1,700** |
| Deploys a producción | **3** |
| Bugs resueltos | **3** (float/NaN en Excel, flag_pagada incorrecto, Mixed Content) |
| Features nuevas | **2** (visor PDF, proxy documentos) |

---

## 🔜 Próximos Pasos (Ver ROADMAP.md)

### Fase 1 — Integración de Pagos (Semana 1-2 de Marzo)
1. Importar 160,822 registros de `PAGTOTAL_08022026.xlsx`
2. Vincular pagos a pólizas existentes
3. Recalcular métricas de cobranza con datos reales
4. Actualizar conciliación AXA

### Fase 2 — Pipeline de Solicitudes Real (Semana 3-4 de Marzo)
1. Importar 232 solicitudes del Concentrado AXA
2. Importar 3,937 eventos de etapas
3. Actualizar Kanban con datos reales
4. Timeline visual de etapas por solicitud

### Fase 3 — Dashboard Ejecutivo Formal (Semana 1 de Abril)
1. Implementar KPIs del documento "Paso a Paso"
2. Tabla de metas configurables
3. Comparativo interanual

---

*Reporte generado: 2 de Marzo, 2026 13:20 CST*
*MAG Sistema v0.2.0 | Promotoría MAG · AXA Seguros México*
