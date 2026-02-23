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
from api.routers import (
    router_dashboard,
    router_polizas,
    router_agentes,
    router_conciliacion,
    router_importacion,
    router_exportacion,
)

IS_DEMO = os.getenv("DEMO_MODE", "true").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
if FRONTEND_URL:
    ALLOWED_ORIGINS.append(FRONTEND_URL.rstrip("/"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[MAG] Iniciando MAG Sistema API...")
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
    title="MAG Sistema API",
    description="Backend FastAPI para gestion de polizas Vida y GMM — Promotoria MAG / AXA Seguros",
    version="0.1.0",
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
app.include_router(router_importacion)
app.include_router(router_exportacion)


@app.get("/", tags=["Sistema"])
def root():
    return {
        "sistema": "MAG Sistema API",
        "version": "0.1.0",
        "promotoria": "MAG - AXA Seguros Mexico",
        "ramos": ["Vida Individual", "GMM Individual"],
        "docs": "/docs",
        "status": "operativo",
        "demo": IS_DEMO,
    }


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
