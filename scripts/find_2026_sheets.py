
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
for name in wb.sheetnames:
    if '2026' in name:
        print(f"2026 RELEVANT SHEET: {name}")
wb.close()
