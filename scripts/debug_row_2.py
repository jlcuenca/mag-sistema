
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_row_2():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    row = next(ws.iter_rows(min_row=2, max_row=2, values_only=True))
    for i, val in enumerate(row):
        print(f"{i+1}: {val}")
    wb.close()

check_row_2()
