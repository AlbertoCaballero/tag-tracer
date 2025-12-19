import pandas as pd

try:
    xls = pd.ExcelFile('assets/sample-config.xlsx')
    print("Sheet names:", xls.sheet_names)
    for sheet_name in xls.sheet_names:
        print(f"\n--- {sheet_name} ---")
        df = xls.parse(sheet_name)
        print(df.head())
except FileNotFoundError:
    print("Excel file not found.")
except Exception as e:
    print(f"An error occurred: {e}")