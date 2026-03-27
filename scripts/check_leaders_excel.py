
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_leaders():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    leaders = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break # Safety
        
        ramo = str(row[2]).upper()
        neta = float(row[10] or 0)
        anio = str(row[18])
        lider = str(row[26]) # Index 26 = Col 27
        
        if anio == "2025" and ramo == "GAMMA FLEX IND.":
            leaders[lider] = leaders.get(lider, 0) + neta
            
    print("\nLEADERS FOR 2025 GAMMA FLEX IND.:")
    for k, v in sorted(leaders.items(), key=lambda x: x[1], reverse=True):
        print(f"{k}: {v:,.2f}")
    
    wb.close()

check_leaders()
