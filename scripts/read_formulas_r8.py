
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def read_summary_row8_formulas():
    wb = openpyxl.load_workbook(FILE_PATH, data_only=False, read_only=False, keep_vba=True)
    ws = wb["RESUMEN VIDA Y GMM"]
    # Scan Row 8 specifically
    targets = ['AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ', 'BA', 'BB']
    for t in targets:
        cell = ws[f"{t}8"]
        print(f"{t}8: {cell.value}")
    wb.close()

read_summary_row8_formulas()
