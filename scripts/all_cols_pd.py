
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "DET 2024"

df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, nrows=50)
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

# Try 2025 too
SHEET_NAME_2 = "DET 2025"
df2 = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME_2, nrows=50)
print(f"\n--- {SHEET_NAME_2} ---")
for i, col in enumerate(df2.columns):
    print(f"{i}: {col}")
