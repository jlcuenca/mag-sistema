
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "DET 2024"

wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
ws = wb[SHEET_NAME]

for r in range(1, 5):
    print(f"Row {r}: {[c.value for c in ws[r]]}")
wb.close()
