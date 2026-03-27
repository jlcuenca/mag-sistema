
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
ws = wb["PRIMA PAGADA"]
headers = [c.value for c in next(ws.iter_rows(max_row=1))]
for i, h in enumerate(headers):
    print(f"{i+1}: {h}")
wb.close()
