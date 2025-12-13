import pandas as pd
from pydantic import BaseModel
from typing import List, Dict, Any

def _parse_string_list(value: str) -> List[str]:
    """
    Parses a string that represents a list, e.g., "[item1, item2]".
    """
    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        # Remove brackets and split by comma
        items = value[1:-1].split(',')
        # Strip whitespace from each item and filter out empty strings
        return [item.strip() for item in items if item.strip()]
    return [value]

class VendorConfig(BaseModel):
    domains: List[str] = []
    query_fields: List[str] = []
    body_fields: List[str] = []
    header_fields: List[str] = []

class PageConfig(BaseModel):
    id: str
    target_url: str
    expected_tags: Dict[str, Any] = {}

class ExcelConfig(BaseModel):
    vendors: Dict[str, VendorConfig] = {}
    pages: List[PageConfig] = []

class ExcelLoader:
    def __init__(self, path: str):
        self.path = path
        try:
            self.workbook = pd.ExcelFile(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at: {path}")

    def load(self) -> ExcelConfig:
        config = ExcelConfig()

        for sheet_name in self.workbook.sheet_names:
            df = self.workbook.parse(sheet_name).dropna(how='all')
            if sheet_name == 'pages':
                                for _, row in df.iterrows():
                                    page = PageConfig(id=row['id'], target_url=row['target-url'])
                                    for col in df.columns:
                                        if col not in ['id', 'target-url']:
                                            if pd.notna(row[col]):
                                                if col == 'vendors':
                                                    page.expected_tags[col] = _parse_string_list(row[col])
                                                else:
                                                    page.expected_tags[col] = row[col]
                                    config.pages.append(page)
            else: # Vendor sheet
                vendor_name = sheet_name
                vendor_config = VendorConfig()

                if len(df.columns) < 2:
                    continue
                
                key_col = df.columns[0]
                val_col = df.columns[1]

                for _, row in df.iterrows():
                    key = row[key_col]
                    value = row[val_col]

                    if pd.isna(key) or pd.isna(value):
                        continue

                    if key == 'domain':
                        vendor_config.domains.append(value)
                    elif key == 'query-fields':
                        vendor_config.query_fields.extend(_parse_string_list(value))
                    elif key == 'body-field' or key == 'body-fields':
                        vendor_config.body_fields.extend(_parse_string_list(value))
                    elif key == 'header-fields':
                        vendor_config.header_fields.extend(_parse_string_list(value))

                config.vendors[vendor_name] = vendor_config

        return config