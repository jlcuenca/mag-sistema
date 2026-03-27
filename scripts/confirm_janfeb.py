
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def confirm_janfeb_match():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    total_new = 0
    total_sub = 0
    
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        neta = float(row[10] or 0)
        endoso = str(row[5])
        # Column 46 is MES? Let's check headers again.
        # Wait! Row[45] was MES in my theory.
        mes_val = row[45] # Index 45 (Col 46)
        contabiliza_2024 = row[44] # Index 44 (Col 45)
        
        if agente == "644717" and anio == "2024" and str(row[2]).upper() == 'GAMMA FLEX IND.':
            if contabiliza_2024 and isinstance(contabiliza_2024, (int,float)) and contabiliza_2024 >= 1:
                if mes_val and isinstance(mes_val, (int,float)) and mes_val <= 2:
                    if endoso == "1er. Año":
                        total_new += neta
                    else:
                        total_sub += neta
                        
    print(f"644717 (JAN-FEB 2024): New={total_new:,.2f}, Sub={total_sub:,.2f}")
    wb.close()

confirm_janfeb_match()
