
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def check_vida_filter():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["PRIMA PAGADA"]
    vals = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if i > 255000: break
        
        # 30: PRIMER AÑO VIDA (idx 29)
        v = str(row[29])
        vals[v] = vals.get(v, 0) + 1
    print(vals)
    wb.close()

check_vida_filter()
