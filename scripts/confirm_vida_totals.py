
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def confirm_vida_totals():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    total_2024 = 0
    total_2025 = 0
    
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        # 30: PRIMER AÑO VIDA (idx 29)
        filter_val = str(row[29])
        neta = float(row[10] or 0)
        
        if filter_val == "PRIMER AÑO 2024":
            total_2024 += neta
        elif filter_val == "PRIMER AÑO 2025":
            total_2025 += neta
            
    print(f"CONFIRMED TOTALS FOR VIDA:")
    print(f" 2024 (PRIMER AÑO 2024): {total_2024:,.2f}")
    print(f" 2025 (PRIMER AÑO 2025): {total_2025:,.2f}")
    wb.close()

confirm_vida_totals()
