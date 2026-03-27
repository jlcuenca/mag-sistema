
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def get_row_data(sheet):
    df = pd.read_excel(FILE_PATH, sheet_name=sheet, nrows=5, engine='openpyxl')
    print(f"\n--- {sheet} ---")
    print(df.iloc[0].to_dict())

get_row_data("DET 2024")
get_row_data("DET 2025")
