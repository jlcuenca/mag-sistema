
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def inspect_644717():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    
    print("INSIGHT INTO AGENT 644717 (2024):")
    # 1: agente, 19: Año
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        agente = str(row[0])
        anio = str(row[18])
        ramo = str(row[2])
        
        if agente == "644717" and anio == "2024" and ramo == "GAMMA FLEX IND.":
            # Print ALL columns for this row
            for idx, val in enumerate(row):
                if val and isinstance(val, (int, float)) and val > 100:
                    print(f"Col {idx+1}: {val}")
            print("--- End Row ---")
            if i > 100: break # Only a few rows

    wb.close()

inspect_644717()
