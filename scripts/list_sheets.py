
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

if not os.path.exists(FILE_PATH):
    print(f"File not found: {FILE_PATH}")
else:
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True)
    print(f"Tabs: {wb.sheetnames}")
    wb.close()
