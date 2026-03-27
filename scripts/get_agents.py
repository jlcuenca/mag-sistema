
import openpyxl
import os

FILE_PATH = r"c:\Users\jlcue\Documents\mag-sistema\ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"

def get_all_mag_agents():
    wb = openpyxl.load_workbook(FILE_PATH, read_only=True, data_only=True)
    ws = wb["RESUMEN VIDA Y GMM"]
    agents = []
    # Row 10 to whatever row is not empty
    for r in range(10, 100):
        code = ws.cell(row=r, column=1).value
        if not code: break
        agents.append(str(code))
    wb.close()
    return agents

agents = get_all_mag_agents()
print(f"MAG AGENTS LIST ({len(agents)}):")
print(agents)
