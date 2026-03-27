
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_ramo_644717():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    # Ramo: Col 3 (idx 2)
    sums_by_ramo = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        ramo = str(row[2]).upper()
        
        if agente == "644717" and anio == "2024":
            sums_by_ramo[ramo] = sums_by_ramo.get(ramo, 0) + neta
            
    print(f"Agent 644717 in 2024 by Ramo:")
    for k, v in sums_by_ramo.items():
        print(f" {k}: {v:,.2f}")
    wb.close()

check_ramo_644717()
