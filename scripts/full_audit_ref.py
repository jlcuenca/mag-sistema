
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def analyze_sheet(sheet):
    print(f"\n--- ANALYZING {sheet} ---")
    df = pd.read_excel(FILE_PATH, sheet_name=sheet, engine='openpyxl')
    
    # Ramo column is usually Index 9 (J)
    ramo_col = df.columns[9]
    print(f"Ramo column detected as: {ramo_col}")
    
    # New/Sub column is usually Column 40 (Unnamed: 40)
    # But for 2025 maybe it is different?
    flag_col = None
    for c in df.columns:
        if "Unnamed: 40" in str(c) or "AN" in str(c): flag_col = c
    if not flag_col:
        # Fallback to the very last column if it looks like a flag
        flag_col = df.columns[-1]
    
    print(f"Flag column detected as: {flag_col}")
    
    # Filter for VIDA
    df_vida = df[df[ramo_col].astype(str).str.upper() == 'VIDA']
    print(f"Total VIDA policies in sheet: {len(df_vida)}")
    
    # Check counts by flag
    if flag_col in df_vida.columns:
        counts = df_vida[flag_col].value_counts(dropna=False)
        print("Flag distribution (Vida):")
        print(counts)
        
        # Calculate sums
        prima_col = df.columns[10] # K is index 10?
        print(f"Prima Neta column detected as: {prima_col}")
        sums = df_vida.groupby(flag_col)[prima_col].sum()
        print("Prima Neta distribution (Vida):")
        print(sums)
    else:
        print("Flag column NOT found!")

analyze_sheet("DET 2024")
analyze_sheet("DET 2025")
