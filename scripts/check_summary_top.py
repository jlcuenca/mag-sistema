
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_summary_top():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["RESUMEN VIDA Y GMM"]
    for r in range(1, 15):
        row_data = [ws.cell(row=r, column=c).value for c in range(40, 56)]
        print(f"Row {r}: {row_data}")
    wb.close()

check_summary_top()
