"""Test dashboard API endpoints."""
import requests
import json

BASE = "http://localhost:8000"

# Test dashboard principal
print("=== Dashboard 2025 ===")
r = requests.get(f"{BASE}/dashboard?anio=2025")
d = r.json()
for k, v in d.items():
    if isinstance(v, (int, float)):
        print(f"  {k}: {v:,.2f}" if isinstance(v, float) else f"  {k}: {v}")
    elif isinstance(v, list) and len(v) > 0:
        print(f"  {k}: [{len(v)} items]")

print()
print("=== Dashboard Ejecutivo 2025 ===")
r = requests.get(f"{BASE}/dashboard/ejecutivo?anio=2025")
if r.status_code == 200:
    d = r.json()
    if "comparativo" in d:
        print(f"  comparativo: {len(d['comparativo'])} ramos")
    if "top_agentes" in d:
        print(f"  top_agentes: {len(d['top_agentes'])} agentes")
    if "kpis" in d:
        print(f"  kpis: {json.dumps(d['kpis'], indent=2)[:500]}")
else:
    print(f"  Error: {r.status_code} - {r.text[:200]}")

print()
print("=== Cobranza 2025 ===")
r = requests.get(f"{BASE}/cobranza?anio=2025")
if r.status_code == 200:
    d = r.json()
    if "resumen" in d:
        print(f"  resumen: {json.dumps(d['resumen'], indent=2)[:500]}")
else:
    print(f"  Error: {r.status_code} - {r.text[:200]}")

print()
print("=== Finanzas 2025 ===")
r = requests.get(f"{BASE}/finanzas?anio=2025")
if r.status_code == 200:
    d = r.json()
    if "resumen" in d:
        print(f"  resumen: {json.dumps(d['resumen'], indent=2)[:500]}")
    if "ingresos_egresos" in d:
        print(f"  ingresos_egresos: {len(d['ingresos_egresos'])} meses")
else:
    print(f"  Error: {r.status_code} - {r.text[:200]}")

print()
print("=== Polizas (page 1) ===")
r = requests.get(f"{BASE}/polizas?page=1&limit=5&anio=2025")
if r.status_code == 200:
    d = r.json()
    print(f"  total: {d.get('total', 0)}")
    print(f"  pages: {d.get('pages', 0)}")
    if "data" in d and len(d["data"]) > 0:
        first = d["data"][0]
        print(f"  ejemplo: {first.get('poliza_original')} - {first.get('prima_neta')} - {first.get('mystatus')}")
else:
    print(f"  Error: {r.status_code} - {r.text[:200]}")

print()
print("=== TESTS COMPLETADOS ===")
