
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

AGENT_CODES = ['644717', '625328', '629094', '48561', '47968', '645658', '646069', '633890', '647749', '648986', '48357', '631611', '55538', '48847', '622011'] # Subset for now

def check_90_sum():
    # I already found 90 agents in get_agents.py. I'll take a larger subset
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    # 2024 Total Sum
    sum_2024 = 0
    # Agente: 0, Ramo: 2, Neta: 10, Año: 18
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        ramo = str(row[2]).upper()
        
        # We need a way to filter for the EXACT "Vida" product the summary tab uses.
        # Maybe it filter by 'CUENTA O NO CUENTA' (Col 28)?
        cuenta = row[27] 
        
        if anio == "2024" and ramo == "GAMMA FLEX IND." and str(cuenta) == "1":
            sum_2024 += neta
            
    print(f"Total for 2024 (GAMMA FLEX IND + CUENTA=1): {sum_2024:,.2f}")
    wb.close()

check_90_sum()
