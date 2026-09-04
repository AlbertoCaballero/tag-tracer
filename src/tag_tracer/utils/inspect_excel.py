import pandas as pd
from pathlib import Path

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "assets" / "sample-config.xlsx"

try:
    xls = pd.ExcelFile(SAMPLE_CONFIG)
    print("Sheet names:", xls.sheet_names)
    for sheet_name in xls.sheet_names:
        print(f"\n--- {sheet_name} ---")
        df = xls.parse(sheet_name)
        print(df.head())
except FileNotFoundError:
    print("Excel file not found.")
except Exception as e:
    print(f"An error occurred: {e}")