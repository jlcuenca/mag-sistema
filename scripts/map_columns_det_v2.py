
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
SHEET_NAME = "DET 2024"

wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
ws = wb[SHEET_NAME]

headers = [c.value for c in ws[1]]
print(f"Header length: {len(headers)}")
for i, h in enumerate(headers[40:]):
    print(f"{i+41}: {h}")

wb.close()
