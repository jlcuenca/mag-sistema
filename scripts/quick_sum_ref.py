
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def quick_sum(sheet):
    print(f"\n--- QUICK SUM {sheet} ---")
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb[sheet]
    
    total_vida = 0
    c_vida = 0
    total_gmm = 0
    c_gmm = 0
    
    # Iterate skipping header
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i % 1000 == 0 and i > 0: print(f"Prcesados {i}...")
        
        # J = 10, K = 11
        ramo = row[9] 
        neto = row[10]
        
        if str(ramo).upper() == "VIDA":
            total_vida += (neto or 0)
            c_vida += 1
        elif str(ramo).upper() == "GMM":
            total_gmm += (neto or 0)
            c_gmm += 1
            
    print(f"VIDA: Count={c_vida}, Sum={total_vida:,.2f}")
    print(f"GMM:  Count={c_gmm}, Sum={total_gmm:,.2f}")
    wb.close()

quick_sum("DET 2024")
quick_sum("DET 2025")
