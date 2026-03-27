
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_cuenta():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    # 28:idx 27 (Cuenta)
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        cuenta = row[27] 
        is_new = row[34]
        
        if agente == "644717" and anio == "2024" and str(cuenta) == "1":
            print(f"Countable Payment: Neta={neta}, New={is_new}, Desc={row[3]}") # Contratante Col 4?
            
    wb.close()

check_cuenta()
