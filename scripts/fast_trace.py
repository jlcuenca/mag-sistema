
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
POL_SEARCH = "76384" # Suffix

def fast_trace():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    print(f"Tracing {POL_SEARCH}...")
    # 5: poliza (idx 4), 6: endoso, 11: neta, 19: Año, 35: Flag Nueva (idx 34)
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        pol = str(row[4])
        if POL_SEARCH in pol:
            print(f"Match: Pol={pol}, Endoso={row[5]}, Año={row[18]}, Neta={row[10]}, FlagNew={row[34]}")
            
    wb.close()

fast_trace()
