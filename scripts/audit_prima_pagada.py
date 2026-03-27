
import pandas as pd
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

df = pd.read_excel(FILE_PATH, sheet_name="PRIMA PAGADA", engine='openpyxl')
print("Years in PRIMA PAGADA (Column 19):")
print(df.iloc[:, 18].value_counts()) # 19th column is index 18
print("\nRamos in PRIMA PAGADA (Column 3):")
print(df.iloc[:, 2].value_counts()) # 3rd column is index 2
print("\nLabels NUEVA NO NUEVA (Column 35):")
print(df.iloc[:, 34].value_counts()) # 35th column is index 34
