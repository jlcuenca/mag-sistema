
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "DET 2024"

print(f"Loading {SHEET_NAME} with pandas...")
df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, nrows=10, engine='openpyxl') # Using nrows is fast
print(df.columns.tolist())
print(df.head())
