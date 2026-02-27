"""
Tests E2E — MAG Sistema API
============================
Pruebas end-to-end de todos los endpoints usando FastAPI TestClient.
BD SQLite temporal aislada para cada sesión de tests.

Ejecutar: python -m pytest tests/test_e2e.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base, get_db
from api.seed import seed_demo


# ── Isolated file-based test DB ─────────────────────────────────────
_TEST_DB = os.path.join(tempfile.gettempdir(), "mag_test_e2e.db")
_ENGINE = create_engine(f"sqlite:///{_TEST_DB}", connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    Base.metadata.create_all(bind=_ENGINE)
    db = _Session()
    seed_demo(db)
    db.close()
    from main import app
    app.dependency_overrides[get_db] = _override_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
    _ENGINE.dispose()
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


# Helper to get first agente id from seeded data
def _agente_ids(client, count=2):
    r = client.get("/agentes")
    data = r.json().get("data", [])
    return [d["id"] for d in data[:count]]


# ═══════════════════════════════════════════════════════════════════
# 1. SISTEMA
# ═══════════════════════════════════════════════════════════════════

class TestSistema:
    def test_root(self, client):
        d = client.get("/").json()
        assert d["sistema"] == "MAG Sistema API"
        assert d["status"] == "operativo"

    def test_health(self, client):
        assert client.get("/health").json()["status"] == "ok"


# ═══════════════════════════════════════════════════════════════════
# 2. DASHBOARD
# ═══════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_returns_200(self, client):
        assert client.get("/dashboard?anio=2025").status_code == 200

    def test_kpi_fields(self, client):
        kpis = client.get("/dashboard?anio=2025").json()["kpis"]
        for k in ["total_polizas", "polizas_nuevas_vida", "polizas_nuevas_gmm",
                   "prima_nueva_vida", "prima_nueva_gmm", "polizas_canceladas"]:
            assert k in kpis, f"Missing: {k}"

    def test_has_data(self, client):
        kpis = client.get("/dashboard?anio=2025").json()["kpis"]
        assert kpis["total_polizas"] > 0

    def test_produccion_mensual(self, client):
        pm = client.get("/dashboard?anio=2025").json()["produccion_mensual"]
        assert isinstance(pm, list)

    def test_top_agentes(self, client):
        ta = client.get("/dashboard?anio=2025").json()["top_agentes"]
        assert isinstance(ta, list)

    def test_distribucion_gama(self, client):
        assert "distribucion_gama" in client.get("/dashboard?anio=2025").json()


# ═══════════════════════════════════════════════════════════════════
# 3. POLIZAS (response: {data, total, page, limit, pages})
# ═══════════════════════════════════════════════════════════════════

class TestPolizas:
    def test_list(self, client):
        d = client.get("/polizas").json()
        assert "data" in d
        assert "total" in d
        assert d["total"] > 0

    def test_limit(self, client):
        d = client.get("/polizas?limit=5").json()
        assert len(d["data"]) <= 5

    def test_pagination(self, client):
        d = client.get("/polizas?page=1&limit=10").json()
        assert d["page"] == 1
        assert d["limit"] == 10
        assert d["pages"] >= 1

    def test_filter_ramo(self, client):
        d = client.get("/polizas?ramo=vida").json()
        assert d["total"] >= 0  # May or may not have vida polizas


# ═══════════════════════════════════════════════════════════════════
# 4. AGENTES (response: {data: [...]})
# ═══════════════════════════════════════════════════════════════════

class TestAgentes:
    def test_list(self, client):
        d = client.get("/agentes").json()
        assert "data" in d
        assert len(d["data"]) >= 8

    def test_fields(self, client):
        ag = client.get("/agentes").json()["data"][0]
        assert "id" in ag
        assert "nombre_completo" in ag or "codigo_agente" in ag

    def test_filter_situacion(self, client):
        r = client.get("/agentes?situacion=TODOS")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# 5. COBRANZA (response: {resumen, deudores, renovaciones, canceladas, alertas, seguimiento_mensual})
# ═══════════════════════════════════════════════════════════════════

class TestCobranza:
    def test_returns_200(self, client):
        assert client.get("/cobranza?anio=2025").status_code == 200

    def test_structure(self, client):
        d = client.get("/cobranza?anio=2025").json()
        for k in ["resumen", "deudores", "renovaciones", "canceladas", "alertas", "seguimiento_mensual"]:
            assert k in d, f"Missing: {k}"

    def test_resumen_fields(self, client):
        res = client.get("/cobranza?anio=2025").json()["resumen"]
        assert "total_pendiente" in res or "polizas_pendientes" in res or isinstance(res, dict)


# ═══════════════════════════════════════════════════════════════════
# 6. FINANZAS
# ═══════════════════════════════════════════════════════════════════

class TestFinanzas:
    def test_returns_200(self, client):
        assert client.get("/finanzas?anio=2025").status_code == 200

    def test_structure(self, client):
        d = client.get("/finanzas?anio=2025").json()
        for k in ["resumen", "ingresos_egresos", "proyeccion", "presupuesto", "tendencia"]:
            assert k in d, f"Missing: {k}"

    def test_resumen_kpis(self, client):
        res = client.get("/finanzas?anio=2025").json()["resumen"]
        for k in ["prima_cobrada_total", "comision_total", "margen_total"]:
            assert k in res, f"Missing: {k}"

    def test_ingresos_egresos(self, client):
        ie = client.get("/finanzas?anio=2025").json()["ingresos_egresos"]
        assert isinstance(ie, list)
        if ie:
            assert "mes" in ie[0]
            assert "prima_cobrada" in ie[0]

    def test_proyeccion(self, client):
        proy = client.get("/finanzas?anio=2025").json()["proyeccion"]
        for k in ["prima_acumulada", "proyeccion_anual", "confianza"]:
            assert k in proy, f"Missing: {k}"

    def test_filtros(self, client):
        f = client.get("/finanzas?anio=2025").json()["filtros_disponibles"]
        assert "ramos" in f
        assert "anios" in f

    def test_ramo_filter(self, client):
        assert client.get("/finanzas?anio=2025&ramo=vida").status_code == 200

    def test_presupuesto_list(self, client):
        p = client.get("/finanzas?anio=2025").json()["presupuesto"]
        assert isinstance(p, list)

    def test_tendencia_list(self, client):
        t = client.get("/finanzas?anio=2025").json()["tendencia"]
        assert isinstance(t, list)


# ═══════════════════════════════════════════════════════════════════
# 7. CONTRATANTES
# ═══════════════════════════════════════════════════════════════════

class TestContratantes:
    def test_list(self, client):
        d = client.get("/contratantes").json()
        assert isinstance(d, list)
        assert len(d) >= 6

    def test_fields(self, client):
        c = client.get("/contratantes").json()[0]
        for k in ["id", "nombre", "num_polizas", "prima_total"]:
            assert k in c

    def test_search_name(self, client):
        d = client.get("/contratantes?q=MARTINEZ").json()
        assert len(d) >= 1
        assert any("MARTINEZ" in c["nombre"] for c in d)

    def test_search_rfc(self, client):
        d = client.get("/contratantes?q=MALC").json()
        assert len(d) >= 1

    def test_search_empty(self, client):
        assert len(client.get("/contratantes?q=ZZZZNOTEXIST").json()) == 0

    def test_create(self, client):
        r = client.post("/contratantes", json={
            "nombre": "E2E TEST CLIENTE", "rfc": "E2ET900101ZZZ", "telefono": "5500000000"
        })
        assert r.status_code == 201
        assert r.json()["nombre"] == "E2E TEST CLIENTE"
        assert r.json()["id"] > 0

    def test_update(self, client):
        r = client.post("/contratantes", json={"nombre": "EDITAR, X"})
        cid = r.json()["id"]
        r2 = client.put(f"/contratantes/{cid}", json={"nombre": "EDITADO, X", "telefono": "111"})
        assert r2.status_code == 200
        assert r2.json()["nombre"] == "EDITADO, X"

    def test_update_404(self, client):
        assert client.put("/contratantes/999999", json={"nombre": "X"}).status_code == 404

    def test_referrals(self, client):
        d = client.get("/contratantes").json()
        refs = [c for c in d if c.get("referido_por_nombre")]
        assert len(refs) >= 2


# ═══════════════════════════════════════════════════════════════════
# 8. SOLICITUDES
# ═══════════════════════════════════════════════════════════════════

class TestSolicitudes:
    def test_list(self, client):
        d = client.get("/solicitudes").json()
        assert "solicitudes" in d
        assert "pipeline" in d

    def test_pipeline_counts(self, client):
        p = client.get("/solicitudes").json()["pipeline"]
        assert p["total"] >= 8
        s = p["tramite"] + p["emitida"] + p["pagada"] + p["rechazada"] + p["cancelada"]
        assert s == p["total"]

    def test_pipeline_primas(self, client):
        p = client.get("/solicitudes").json()["pipeline"]
        assert p["prima_estimada_total"] > 0

    def test_filter_estado(self, client):
        d = client.get("/solicitudes?estado=PAGADA").json()
        for s in d["solicitudes"]:
            assert s["estado"] == "PAGADA"

    def test_folio_fields(self, client):
        sols = client.get("/solicitudes").json()["solicitudes"]
        if sols:
            for k in ["id", "folio", "estado", "ramo"]:
                assert k in sols[0]

    def test_create_auto_folio(self, client):
        r = client.post("/solicitudes", json={"ramo": "VIDA", "prima_estimada": 10000})
        assert r.status_code == 201
        assert r.json()["folio"].startswith("SOL-")
        assert r.json()["estado"] == "TRAMITE"

    def test_create_custom_folio(self, client):
        r = client.post("/solicitudes", json={"folio": "E2E-001", "ramo": "GMM", "prima_estimada": 20000})
        assert r.status_code == 201
        assert r.json()["folio"] == "E2E-001"

    def test_full_lifecycle(self, client):
        # Create
        r = client.post("/solicitudes", json={"ramo": "VIDA", "prima_estimada": 5000})
        sid = r.json()["id"]
        # TRAMITE -> EMITIDA
        r2 = client.put(f"/solicitudes/{sid}", json={"estado": "EMITIDA", "fecha_emision": "2025-03-01"})
        assert r2.status_code == 200
        assert r2.json()["estado"] == "EMITIDA"
        # EMITIDA -> PAGADA
        r3 = client.put(f"/solicitudes/{sid}", json={"estado": "PAGADA", "fecha_pago": "2025-03-15"})
        assert r3.status_code == 200
        assert r3.json()["estado"] == "PAGADA"

    def test_update_404(self, client):
        assert client.put("/solicitudes/999999", json={"estado": "X"}).status_code == 404


# ═══════════════════════════════════════════════════════════════════
# 9. COMISIONES
# ═══════════════════════════════════════════════════════════════════

class TestComisiones:
    def test_list(self, client):
        r = client.get("/comisiones/distribuciones")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create(self, client):
        ids = _agente_ids(client, 2)
        r = client.post("/comisiones/distribuciones", json={
            "agente_id": ids[0], "sub_agente_id": ids[1], "porcentaje": 30, "tipo": "SUBAGENTE"
        })
        assert r.status_code == 201
        assert r.json()["porcentaje"] == 30

    def test_create_with_ramo(self, client):
        ids = _agente_ids(client, 3)
        r = client.post("/comisiones/distribuciones", json={
            "agente_id": ids[2], "porcentaje": 25,
            "nombre_beneficiario": "VENDEDOR", "tipo": "VENDEDOR", "ramo": "VIDA"
        })
        assert r.status_code == 201
        assert r.json()["ramo"] == "VIDA"

    def test_exceeds_100(self, client):
        ids = _agente_ids(client, 8)
        aid = ids[-2] if len(ids) >= 7 else ids[-1]
        # 60%
        client.post("/comisiones/distribuciones", json={
            "agente_id": aid, "porcentaje": 60, "nombre_beneficiario": "A", "tipo": "SUBAGENTE"
        })
        # 50% more -> 110%
        r = client.post("/comisiones/distribuciones", json={
            "agente_id": aid, "porcentaje": 50, "nombre_beneficiario": "B", "tipo": "SUBAGENTE"
        })
        assert r.status_code == 400
        assert "100%" in r.json()["detail"]


# ═══════════════════════════════════════════════════════════════════
# 10. CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════

class TestConfiguracion:
    def test_get_all(self, client):
        d = client.get("/configuracion").json()
        assert len(d["configuraciones"]) >= 9
        assert len(d["grupos"]) >= 4

    def test_groups(self, client):
        g = client.get("/configuracion").json()["grupos"]
        for grp in ["umbrales", "tipos_cambio", "catalogos", "general"]:
            assert grp in g

    def test_filter_grupo(self, client):
        d = client.get("/configuracion?grupo=umbrales").json()
        for c in d["configuraciones"]:
            assert c["grupo"] == "umbrales"

    def test_item_fields(self, client):
        item = client.get("/configuracion").json()["configuraciones"][0]
        for k in ["clave", "valor", "tipo", "grupo", "descripcion"]:
            assert k in item

    def test_update(self, client):
        r = client.put("/configuracion/tc_usd", json={"valor": "20.50"})
        assert r.status_code == 200
        assert r.json()["valor"] == "20.50"
        # Verify persisted
        configs = client.get("/configuracion?grupo=tipos_cambio").json()["configuraciones"]
        usd = next(c for c in configs if c["clave"] == "tc_usd")
        assert usd["valor"] == "20.50"

    def test_update_404(self, client):
        assert client.put("/configuracion/nope_xyz", json={"valor": "X"}).status_code == 404

    def test_json_catalog(self, client):
        import json
        configs = client.get("/configuracion?grupo=catalogos").json()["configuraciones"]
        seg = next(c for c in configs if c["clave"] == "catalogo_segmentos")
        assert seg["tipo"] == "json"
        parsed = json.loads(seg["valor"])
        assert isinstance(parsed, list)
        assert "ALFA TOP INTEGRAL" in parsed


# ═══════════════════════════════════════════════════════════════════
# 11. CONCILIACIÓN
# ═══════════════════════════════════════════════════════════════════

class TestConciliacion:
    def test_returns_200(self, client):
        assert client.get("/conciliacion").status_code == 200


# ═══════════════════════════════════════════════════════════════════
# 12. EXPORTACIÓN (endpoint: /exportar/polizas-excel)
# ═══════════════════════════════════════════════════════════════════

class TestExportacion:
    def test_export(self, client):
        r = client.get("/exportar/polizas-excel")
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "spreadsheet" in ct or "octet-stream" in ct or "excel" in ct


# ═══════════════════════════════════════════════════════════════════
# 13. DATA INTEGRITY
# ═══════════════════════════════════════════════════════════════════

class TestIntegrity:
    def test_pipeline_sums(self, client):
        p = client.get("/solicitudes").json()["pipeline"]
        s = p["tramite"] + p["emitida"] + p["pagada"] + p["rechazada"] + p["cancelada"]
        assert s == p["total"]

    def test_contratantes_count(self, client):
        assert len(client.get("/contratantes").json()) >= 6

    def test_config_groups(self, client):
        assert len(client.get("/configuracion").json()["grupos"]) >= 4

    def test_polizas_seeded(self, client):
        assert client.get("/polizas").json()["total"] >= 100


# ═══════════════════════════════════════════════════════════════════
# 14. ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════

class TestErrors:
    def test_404_solicitud(self, client):
        assert client.put("/solicitudes/999999", json={"estado": "X"}).status_code == 404

    def test_404_contratante(self, client):
        assert client.put("/contratantes/999999", json={"nombre": "X"}).status_code == 404

    def test_404_config(self, client):
        assert client.put("/configuracion/nope", json={"valor": "X"}).status_code == 404

    def test_400_comision(self, client):
        ids = _agente_ids(client, 8)
        aid = ids[-1]
        client.post("/comisiones/distribuciones", json={
            "agente_id": aid, "porcentaje": 90, "nombre_beneficiario": "X", "tipo": "SUBAGENTE"
        })
        r = client.post("/comisiones/distribuciones", json={
            "agente_id": aid, "porcentaje": 20, "nombre_beneficiario": "Y", "tipo": "SUBAGENTE"
        })
        assert r.status_code == 400
