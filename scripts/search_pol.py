
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
POL_SEARCH = "0076384A"

print(f"Searching for {POL_SEARCH} in DET 2024...")
df = pd.read_excel(FILE_PATH, sheet_name="DET 2024", engine='openpyxl')
# Normalize policy column (remove leading zeros if any, or etc)
df['poliza_clean'] = df['poliza'].astype(str).str.strip()

match = df[df['poliza_clean'].str.contains(POL_SEARCH)]
if not match.empty:
    print("Found in Excel!")
    print(match)
else:
    print("NOT found in Excel.")
