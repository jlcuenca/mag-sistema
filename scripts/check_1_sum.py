
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_1_sum():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    sums = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        cuenta = str(row[27])
        if cuenta == "1":
            anio = str(row[18])
            neta = float(row[10] or 0)
            ramo = str(row[2])
            
            key = (anio, ramo)
            sums[key] = sums.get(key, 0) + neta
            
    print("\nSUMS FOR CUENTA='1':")
    for k, v in sorted(sums.items()):
        print(f"{k}: {v:,.2f}")
    wb.close()

check_1_sum()
