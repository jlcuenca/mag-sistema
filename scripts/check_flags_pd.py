
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

df = pd.read_excel(FILE_PATH, sheet_name="DET 2024", engine='openpyxl')
print(f"Unnamed: 40 values for 2024:\n{df['Unnamed: 40'].value_counts()}")

df2 = pd.read_excel(FILE_PATH, sheet_name="DET 2025", engine='openpyxl')
print(f"\nUnnamed: 40 values for 2025:\n{df2['Unnamed: 40'].value_counts()}")
