
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def fast_stat_openpyxl():
    print(f"Opening {FILE_PATH} (100MB)...")
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    stats = {} # (Año, Ramo) -> sum(neta)
    
    # 3: ramo (idx 2), 11: neta (idx 10), 19: Año (idx 18)
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i % 10000 == 0 and i > 0: 
            print(f"Processed {i} rows...")
        
        try:
            ramo = str(row[2]).upper()
            neta = float(row[10] or 0)
            anio = str(row[18])
            
            key = (anio, ramo)
            stats[key] = stats.get(key, 0) + neta
        except:
            continue
            
    print("\nSTATISTICS (Año, Ramo) -> Sum(Neta):")
    for k, v in sorted(stats.items()):
        print(f"{k}: {v:,.2f}")
    
    wb.close()

fast_stat_openpyxl()
