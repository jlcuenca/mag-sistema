
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def read_summary_r8_readonly():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=False)
    ws = wb["RESUMEN VIDA Y GMM"]
    for t in ['AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ', 'BA', 'BB']:
        print(f"{t}8: {ws[f'{t}8'].value}")
    wb.close()

read_summary_r8_readonly()
