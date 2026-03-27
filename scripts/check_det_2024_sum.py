
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_det_2024_sum():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["DET 2024"]
    
    total = 0
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 1000: break
        # Column 11: Neta? Col 1: poliza
        try:
            val = float(row[10] or 0)
            total += val
        except: pass
        
    print(f"DET 2024 Summerized first 1000 rows sum column 11: {total}")
    wb.close()

check_det_2024_sum()
