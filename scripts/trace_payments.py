
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
POL_SEARCH = "0076384A"

df = pd.read_excel(FILE_PATH, sheet_name="PRIMA PAGADA", engine='openpyxl')
# Normalizar poliza (columna 5, indice 4)
df['pol_norm'] = df.iloc[:, 4].astype(str).str.strip().str.replace(r'^0+', '', regex=True)

match = df[df['pol_norm'].str.contains(POL_SEARCH)]
print(f"Payments found for {POL_SEARCH}:")
print(match[['Endoso', 'Año', 'neta', 'PRIME AÑO', 'NUEVA NO NUEVA']]) # Check exact labels
