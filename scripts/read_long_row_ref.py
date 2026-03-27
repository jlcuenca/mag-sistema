
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def read_long_row():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["DET 2024"]
    row = next(ws.iter_rows(min_row=2, max_row=2, values_only=True))
    for i, val in enumerate(row):
        if val and isinstance(val, (int, float)) and val > 1000:
            print(f"Col {i+1}: {val} (Possible Amount)")
        elif val == "VIDA" or val == "GMM":
             print(f"Col {i+1}: {val} (Ramo)")
    wb.close()

read_long_row()
