
import pandas as pd
import json

excel_path = r"ref\Reporte 08 FEBRERO 2026 BASE VIDA Y GMM VF2 OK ULTIMO (1).xlsm"
policy_number = "1072723H"

def compare_excel_db():
    print(f"Reading Excel: {excel_path} ...")
    # Read only the first 100 columns to find headers
    df = pd.read_excel(excel_path, sheet_name="AUTOMATICO VIDA", header=0)
    
    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Find the row for the policy. Policy is likely in "POLIZA" column.
    # Let's check which column contains the policy number.
    # In Step 1324, Col T (index 19) was "POLIZA".
    policy_col = "POLIZA" if "POLIZA" in df.columns else df.columns[19]
    print(f"Using policy column: {policy_col}")
    
    row = df[df[policy_col].astype(str).str.contains(policy_number, na=False)]
    
    if row.empty:
        print(f"Policy {policy_number} not found in Excel.")
        return

    # Extract the first matching row
    excel_data = row.iloc[0].to_dict()
    
    print("\n=== [ EXCEL VALUES (Row identified) ] ===")
    # Show columns from BE (index 56?)
    # A=0, B=1, ..., Z=25, AA=26, ..., AZ=51, BA=52, BB=53, BC=54, BD=55, BE=56
    columns_from_be = list(df.columns)[56:]
    for col in columns_from_be:
        val = excel_data.get(col)
        print(f"{col:30}: {val}")

compare_excel_db()
