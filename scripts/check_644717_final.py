
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_644717_vida():
    print(f"Opening {FILE_PATH}...")
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    total = 0
    # 1: agente, 11: neta, 19: Año, 30: Filter
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        filt = str(row[29])
        ramo = str(row[2]).upper()
        
        if agente == "644717" and anio == "2024":
            if filt == "PRIMER AÑO 2024" or "PRIMER" in filt:
                total += neta
                # print(f"Row {i}: Neta={neta}, Filt={filt}, Ramo={ramo}")
                
    print(f"Total summed for 644717 with 'PRIMER' filter in 2024: {total:,.2f}")
    wb.close()

check_644717_vida()
