
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_mapping():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    sum_new = 0
    sum_sub = 0
    # Agente: Col 1 (idx 0), Neta: Col 11 (idx 10), Año: Col 19 (idx 18), 
    # Nueva: Col 35 (idx 34)
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        is_new = row[34] # 1 or 0
        
        if agente == "644717" and anio == "2024":
            if is_new == 1:
                sum_new += neta
            else:
                sum_sub += neta
                
    print(f"Agent 644717 in 2024: New={sum_new:,.2f}, Sub={sum_sub:,.2f}")
    wb.close()

check_mapping()
