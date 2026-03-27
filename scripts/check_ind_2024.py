
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_ind_2024():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    total = 0
    # Agente: 0, IND 2024: 45 (idx 44)
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        # We need the amount column that matches 'IND 2024'
        # Maybe IND 2024 IS the amount? 
        # No, index 44 was None in many rows.
        if row[44] and isinstance(row[44], (int, float)):
            total += row[44]
            
    print(f"Global sum of Column 45 (IND 2024): {total:,.2f}")
    wb.close()

check_ind_2024()
