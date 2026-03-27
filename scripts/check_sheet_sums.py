
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_sums(sheet):
    print(f"\n--- {sheet} SUMS ---")
    df = pd.read_excel(FILE_PATH, sheet_name=sheet, engine='openpyxl')
    
    # Ramo column is usually Index 9 (J)
    ramo_col = df.columns[9]
    vida_df = df[df[ramo_col].astype(str).str.upper() == 'VIDA']
    
    # Prima Neta K is Index 10
    prima_col = df.columns[10]
    total_vida = vida_df[prima_col].sum()
    print(f"Total VIDA Prima: {total_vida:,.2f}")
    
    # New/Sub calculation - Column 40 (AN or AO? Check headers length)
    if len(df.columns) >= 41:
        flag_col = df.columns[40] # Column AO
        print(f"Flag col: {flag_col}")
        for flag, group in vida_df.groupby(flag_col):
            print(f"  Flag {flag}: {group[prima_col].sum():,.2f}")

check_sums("DET 2024")
check_sums("DET 2025")
