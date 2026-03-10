"""Upload PAGTOTAL CSV to GCP in chunks of 30K rows."""
import pandas as pd
import requests
import io
import time

API = "https://mag-api-922967332336.us-central1.run.app"
CSV_PATH = "fuentes/PAGTOTAL_202603101502.csv"
CHUNK_SIZE = 30000

print("Reading CSV...")
df = pd.read_csv(CSV_PATH, dtype=str, encoding="latin-1")
total = len(df)
print(f"Total rows: {total}")

chunks = [df.iloc[i:i+CHUNK_SIZE] for i in range(0, total, CHUNK_SIZE)]
print(f"Splitting into {len(chunks)} chunks of ~{CHUNK_SIZE} rows")

for idx, chunk in enumerate(chunks):
    is_first = (idx == 0)
    is_last = (idx == len(chunks) - 1)
    
    csv_buf = io.BytesIO()
    chunk.to_csv(csv_buf, index=False, encoding="utf-8")
    csv_buf.seek(0)
    size_mb = csv_buf.getbuffer().nbytes / 1024 / 1024
    print(f"\nChunk {idx+1}/{len(chunks)}: {len(chunk)} rows ({size_mb:.1f} MB)")
    
    params = {
        "limpiar": "true" if is_first else "false",
        "actualizar_polizas": "true" if is_last else "false",
    }
    
    start = time.time()
    r = requests.post(
        f"{API}/importar/pagtotal",
        params=params,
        files={"archivo": (f"pagtotal_chunk{idx}.csv", csv_buf, "text/csv")},
        timeout=600,
    )
    elapsed = time.time() - start
    
    if r.status_code == 200:
        d = r.json()
        print(f"  OK ({elapsed:.0f}s) - Nuevos: {d.get('registros_nuevos')}, Actualiz: {d.get('registros_actualizados')}")
    else:
        print(f"  ERROR {r.status_code} ({elapsed:.0f}s): {r.text[:300]}")
        break

print("\nDone!")
