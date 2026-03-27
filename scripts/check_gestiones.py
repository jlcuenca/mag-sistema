
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_gestiones():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    gestiones = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        g = str(row[26]) # Col 27
        gestiones[g] = gestiones.get(g, 0) + 1
            
    print("\nGESTIONES (Col 27) distribution:")
    for k, v in sorted(gestiones.items(), key=lambda x: x[1], reverse=True):
        print(f"{k}: {v}")
    
    wb.close()

check_gestiones()
