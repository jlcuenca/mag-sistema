
import zipfile
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

with zipfile.ZipFile(FILE_PATH, 'r') as z:
    with z.open('xl/workbook.xml') as f:
        print(f.read().decode('utf-8')[:5000])
