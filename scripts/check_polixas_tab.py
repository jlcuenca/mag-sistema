
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "POLIZAS VIDA 2024"

try:
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, nrows=2, engine='openpyxl')
    print(df.columns.tolist())
    print(df.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading {SHEET_NAME}: {e}")
