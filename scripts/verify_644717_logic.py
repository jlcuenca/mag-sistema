
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def verify_644717_logic():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    # Formula said: SUMIFS(K:K, F:F, '1er. Año', ...)
    # F: idx 5 (endoso)
    # K: idx 10 (neta)
    # A: idx 0 (agente)
    sum_endoso_1er_anio = 0
    sum_others = 0
    
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        endoso = str(row[5])
        neta = float(row[10] or 0)
        anio = str(row[18])
        ramo = str(row[2]).upper()
        
        if agente == "644717" and anio == "2024" and ramo == 'GAMMA FLEX IND.':
            if endoso == "1er. Año":
                sum_endoso_1er_anio += neta
            else:
                sum_others += neta
                
    print(f"644717 (2024) - '1er. Año' Endoso: {sum_endoso_1er_anio:,.2f}")
    print(f"644717 (2024) - Others (Renewal): {sum_others:,.2f}")
    wb.close()

verify_644717_logic()
