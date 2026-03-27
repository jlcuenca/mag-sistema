
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def fast_audit(sheet):
    print(f"\n--- FAST AUDIT: {sheet} ---")
    # Read only first 50 columns 
    df = pd.read_excel(FILE_PATH, sheet_name=sheet, engine='openpyxl', usecols="A:AZ")
    
    # Ramo J=9
    ramo = df.iloc[:, 9]
    vida_mask = ramo.astype(str).str.upper() == 'VIDA'
    df_vida = df[vida_mask]
    print(f"VIDA rows: {len(df_vida)}")
    
    # Flag AN=39 or AO=40?
    flag = df_vida.iloc[:, 40]
    print(f"Flag counts:\n{flag.value_counts(dropna=False)}")
    
    # Prima K=10? 
    prima = df_vida.iloc[:, 10]
    print(f"Sum of Prima Neta (VIDA): {prima.sum()}")
    
    # Sum by flag
    print("\nSum of Prima Neta by Flag:")
    print(df_vida.groupby(flag.name).iloc[:, 10].sum())

fast_audit("DET 2024")
fast_audit("DET 2025")
