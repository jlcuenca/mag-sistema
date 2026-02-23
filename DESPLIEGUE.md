# 🚀 Guía de Despliegue — MAG Sistema Demo
**Stack:** FastAPI (Render) + Next.js (Vercel) | Fecha: 23 Feb 2026

---

## Resumen de la arquitectura de producción

```
Usuario  →  https://mag-sistema.vercel.app  (Next.js)
                        │  fetch()
                        ▼
              https://mag-api.onrender.com  (FastAPI Python)
                        │  SQLAlchemy
                        ▼
                     SQLite (seed automático en arranque)
```

---

## PASO 1 — Desplegar el Backend (FastAPI) en Render

### 1.1 Crear cuenta en Render
→ https://render.com  (gratis, sin tarjeta de crédito)

### 1.2 Subir el código (sin Git)
Como Git no está instalado, podemos usar la opción de **ZIP**:

1. Comprimir la carpeta `C:\Users\jlcue\Documents\mag\` 
   EXCLUYENDO: `sistema/node_modules/`, `sistema/.next/`, `*.db`
2. En Render → **New +** → **Web Service** → **Deploy without Git**
3. Subir el ZIP

### 1.3 Configuración del servicio en Render
| Campo | Valor |
|-------|-------|
| **Name** | `mag-api` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free |

### 1.4 Variables de entorno en Render
En la sección **Environment Variables**:
| Key | Value |
|-----|-------|
| `DEMO_MODE` | `true` |
| `PYTHONUTF8` | `1` |
| `FRONTEND_URL` | *(se agrega después con la URL de Vercel)* |

### 1.5 Deploy
- Clic en **Create Web Service**
- Esperar ~3 minutos para el build
- La URL final será algo como: `https://mag-api-xxxx.onrender.com`

> ⚠️ El tier gratuito de Render tiene **cold start de ~30 segundos** tras 15 min de inactividad.
> Para un demo importante, visitar la URL del API antes de mostrar el frontend.

---

## PASO 2 — Desplegar el Frontend (Next.js) en Vercel

### 2.1 Crear cuenta en Vercel
→ https://vercel.com  (gratis)

### 2.2 Opción A — Drag & Drop (más fácil sin Git)

1. Construir el frontend:
```powershell
# En PowerShell:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")+";"+[System.Environment]::GetEnvironmentVariable("PATH","User")
$env:NEXT_PUBLIC_API_URL = "https://mag-api-xxxx.onrender.com"  # URL real de Render
cd C:\Users\jlcue\Documents\mag\sistema
npm run build
```

2. Ir a https://vercel.com/new
3. Arrastrar la carpeta `sistema/` completa (incluyendo `.next/`)
4. Vercel la detecta como proyecto Next.js automáticamente

### 2.2 Opción B — Vercel CLI (recomendado)

```powershell
# En PowerShell (desde la carpeta sistema):
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")+";"+[System.Environment]::GetEnvironmentVariable("PATH","User")
$env:NEXT_PUBLIC_API_URL = "https://mag-api-xxxx.onrender.com"
cd C:\Users\jlcue\Documents\mag\sistema

# Login en Vercel (abre el browser):
npx vercel login

# Deploy:
npx vercel --prod
```

### 2.3 Variables de entorno en Vercel
En **Project Settings → Environment Variables**:
| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://mag-api-xxxx.onrender.com` |

### 2.4 Actualizar CORS en Render
Una vez que tengas la URL de Vercel (`https://mag-sistema.vercel.app`):
1. En Render → tu servicio `mag-api` → **Environment**
2. Agregar: `FRONTEND_URL` = `https://mag-sistema.vercel.app`

---

## PASO 3 — Verificar el despliegue

### Checklist
- [ ] `https://mag-api-xxxx.onrender.com/health` → `{"status":"ok"}`
- [ ] `https://mag-api-xxxx.onrender.com/docs` → Swagger UI visible
- [ ] `https://mag-api-xxxx.onrender.com/dashboard?anio=2025` → JSON con KPIs
- [ ] `https://mag-sistema.vercel.app` → Dashboard cargado con datos

---

## Comandos locales de referencia

```powershell
# Arrancar todo local (2 terminales)

# Terminal 1 — Backend Python:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")+";"+[System.Environment]::GetEnvironmentVariable("PATH","User")
$env:PYTHONUTF8 = "1"
cd C:\Users\jlcue\Documents\mag
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend Next.js:
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")+";"+[System.Environment]::GetEnvironmentVariable("PATH","User")
cd C:\Users\jlcue\Documents\mag\sistema
npm run dev
```

**URLs locales:**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Estructura del repositorio para subir

```
mag/
├── main.py                  # FastAPI entry point
├── requirements.txt         # Dependencias Python
├── render.yaml              # Config Render (opcional)
├── .gitignore
├── api/
│   ├── __init__.py
│   ├── database.py          # Modelos SQLAlchemy
│   ├── rules.py             # Motor de reglas de negocio
│   ├── schemas.py           # Pydantic schemas
│   ├── routers.py           # Endpoints REST
│   └── seed.py              # Datos de demo
└── sistema/                 # Frontend Next.js
    ├── app/
    ├── components/
    ├── lib/
    ├── public/
    ├── vercel.json
    ├── next.config.mjs
    └── package.json
```

---

*Generado el 23 de febrero de 2026 — MAG Sistema v0.1.0*
