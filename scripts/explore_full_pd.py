
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def explore_sheet(s):
    try:
        df = pd.read_excel(FILE_PATH, sheet_name=s, nrows=3, engine='openpyxl')
        print(f"\n--- SHEET: {s} ---")
        for c in df.columns:
            print(f"{c}: {df.iloc[0].get(c)}")
    except Exception as e:
        print(f"Error reading {s}: {e}")

explore_sheet("DET 2024")
explore_sheet("DET 2025")
