"""
Módulo de configuración por tenant/aseguradora.
Cada instancia de MAG Sistema corre con su propio TENANT.
Las variables de entorno son inyectadas por Terraform via Cloud Run.
"""
import os
from typing import Optional


# ── Configuración del tenant (inyectada por Cloud Run env vars) ──
TENANT_ID: str = os.getenv("TENANT", "axa")
TENANT_DISPLAY_NAME: str = os.getenv("TENANT_DISPLAY_NAME", "AXA Seguros")
TENANT_RAMOS: list[str] = os.getenv(
    "TENANT_RAMOS", "Vida Individual,GMM Individual"
).split(",")

# Entorno
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
IS_DEMO: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

# URLs (se llenan en runtime con outputs de Terraform)
DOCS_BUCKET: str = os.getenv("DOCS_BUCKET", f"magia-docs-{TENANT_ID}")
DOC_BASE_URL: str = os.getenv("DOC_BASE_URL", "")


def get_tenant_config() -> dict:
    """Retorna la configuración completa del tenant actual."""
    return {
        "id": TENANT_ID,
        "display_name": TENANT_DISPLAY_NAME,
        "ramos": TENANT_RAMOS,
        "environment": ENVIRONMENT,
        "is_demo": IS_DEMO,
        "docs_bucket": DOCS_BUCKET,
    }


def get_tenant_branding() -> dict:
    """
    Branding por tenant para el frontend.
    Puede extenderse con colores, logos, etc.
    """
    _BRANDING = {
        "axa": {
            "logo": "/logos/axa.svg",
            "primary_color": "#00008f",
            "accent_color": "#ff1721",
            "name": "AXA Seguros",
        },
        "gnp": {
            "logo": "/logos/gnp.svg",
            "primary_color": "#ff6600",
            "accent_color": "#003366",
            "name": "GNP Seguros",
        },
        "zurich": {
            "logo": "/logos/zurich.svg",
            "primary_color": "#003399",
            "accent_color": "#f0f0f0",
            "name": "Zurich Seguros",
        },
        "chubb": {
            "logo": "/logos/chubb.svg",
            "primary_color": "#002855",
            "accent_color": "#c8102e",
            "name": "Chubb Seguros",
        },
    }
    return _BRANDING.get(TENANT_ID, {
        "logo": "/logos/default.svg",
        "primary_color": "#6366f1",
        "accent_color": "#f59e0b",
        "name": TENANT_DISPLAY_NAME,
    })


def validate_tenant() -> None:
    """Valida que la configuración del tenant sea correcta al arrancar."""
    assert TENANT_ID, "TENANT env var no puede estar vacía"
    assert TENANT_DISPLAY_NAME, "TENANT_DISPLAY_NAME env var no puede estar vacía"
    assert len(TENANT_RAMOS) > 0, "TENANT_RAMOS debe tener al menos un ramo"
    print(f"[MAG-TENANT] ✅ Tenant: {TENANT_ID} ({TENANT_DISPLAY_NAME})")
    print(f"[MAG-TENANT]    Ramos: {', '.join(TENANT_RAMOS)}")
    print(f"[MAG-TENANT]    Demo: {IS_DEMO} | Env: {ENVIRONMENT}")
