
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "DET 2025"

wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
ws = wb[SHEET_NAME]
row_1 = [c.value for c in ws[1]]
print(row_1)
wb.close()
