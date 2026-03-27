
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def find_prima(sheet):
    print(f"\n--- FIND PRIMA IN {sheet} ---")
    df = pd.read_excel(FILE_PATH, sheet_name=sheet, nrows=5)
    for i, h in enumerate(df.columns.tolist()):
        if 'PRIMA' in str(h).upper() or 'PMA' in str(h).upper() or 'NETA' in str(h).upper() or 'EQUIV' in str(h).upper():
            print(f"{i+1}: {h} -> {df.iloc[0, i]}")

find_prima("DET 2024")
find_prima("DET 2025")
