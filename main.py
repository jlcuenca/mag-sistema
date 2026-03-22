"""
MAG Sistema — FastAPI Backend
Promotoria MAG / AXA Seguros — Vida Individual + GMM Individual
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.database import init_db, SessionLocal
from api.seed import seed_demo
from api.tenant import get_tenant_config, get_tenant_branding, validate_tenant, TENANT_ID, TENANT_DISPLAY_NAME
from api.routers import (
    router_dashboard,
    router_polizas,
    router_agentes,
    router_conciliacion,
    router_importacion,
    router_exportacion,
    router_cobranza,
    router_finanzas,
    router_contratantes,
    router_solicitudes,
    router_comisiones,
    router_configuracion,
    router_documentos,
    router_indicadores_sol,
)

IS_DEMO = os.getenv("DEMO_MODE", "true").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://mag-frontend-922967332336.us-central1.run.app",
]
if FRONTEND_URL:
    ALLOWED_ORIGINS.append(FRONTEND_URL.rstrip("/"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[MAG] Iniciando MAG Sistema API — Tenant: {TENANT_ID}")
    validate_tenant()
    init_db()
    db = SessionLocal()
    try:
        seeded = seed_demo(db)
        if seeded:
            print("[MAG] Datos de demo insertados.")
    finally:
        db.close()
    print("[MAG] API lista.")
    yield
    print("[MAG] API detenida.")


app = FastAPI(
    title=f"MAG Sistema API — {TENANT_DISPLAY_NAME}",
    description=f"Backend FastAPI para gestión de pólizas — {TENANT_DISPLAY_NAME}",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEMO else ALLOWED_ORIGINS,
    allow_credentials=not IS_DEMO,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_dashboard)
app.include_router(router_polizas)
app.include_router(router_agentes)
app.include_router(router_conciliacion)
app.include_router(router_cobranza)
app.include_router(router_finanzas)
app.include_router(router_contratantes)
app.include_router(router_solicitudes)
app.include_router(router_comisiones)
app.include_router(router_configuracion)
app.include_router(router_importacion)
app.include_router(router_exportacion)
app.include_router(router_documentos)
app.include_router(router_indicadores_sol)


@app.get("/", tags=["Sistema"])
def root():
    tenant = get_tenant_config()
    return {
        "sistema": "MAG Sistema API",
        "version": "0.2.0",
        "tenant": tenant["id"],
        "promotoria": tenant["display_name"],
        "ramos": tenant["ramos"],
        "docs": "/docs",
        "status": "operativo",
        "demo": tenant["is_demo"],
    }


@app.get("/tenant", tags=["Sistema"])
def tenant_info():
    """Configuración del tenant actual (para frontend)."""
    return {
        **get_tenant_config(),
        "branding": get_tenant_branding(),
    }


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "tenant": TENANT_ID}
