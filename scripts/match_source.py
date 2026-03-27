
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

df = pd.read_excel(FILE_PATH, sheet_name="PRIMA PAGADA", engine='openpyxl')
df['neta'] = pd.to_numeric(df.iloc[:, 10], errors='coerce').fillna(0)
df['anio'] = pd.to_numeric(df.iloc[:, 18], errors='coerce').fillna(0)

# Filter by Vida indicators (Need to confirm which ramo is Vida here)
# Summary says Vida 2024 is 2.45M.
# Let's sum by 'ramo' group
print("Total Prima Neta by Ramo (ALL YEARS):")
print(df.groupby(df.iloc[:, 2]).neta.sum().map('{:,.2f}'.format))

print("\nTotal Prima Neta by Year (ALL RAMOS):")
print(df.groupby('anio').neta.sum().map('{:,.2f}'.format))

# Check Vida candidates for 2024/2025
for yr in [2024, 2025]:
    df_yr = df[df['anio'] == yr]
    print(f"\n--- Analysis for Year {yr} ---")
    print(df_yr.groupby(df_yr.iloc[:, 2]).neta.sum().map('{:,.2f}'.format))
