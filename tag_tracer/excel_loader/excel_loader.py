import ast
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict, Any

from tag_tracer.utils.utils import string_to_list

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
    page_vendors: List[str] = []
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
            data_frame = self.workbook.parse(sheet_name).dropna(how='all')
            if sheet_name == 'pages':
                for _, row in data_frame.iterrows():
                    page = PageConfig(id=row['id'], target_url=row['target-url'], page_vendors=string_to_list(row['vendors']))
                    for col in data_frame.columns:
                        # what is this for?
                        if col not in ['id', 'target-url', 'vendors']:
                            if pd.notna(row[col]):
                                page.expected_tags[col] = row[col]
                    config.pages.append(page)
            else: # Vendor sheets
                vendor_name = sheet_name
                vendor_config = VendorConfig()

                if len(data_frame.columns) < 2:
                    continue
                
                key_col = data_frame.columns[0]
                val_col = data_frame.columns[1]

                for _, row in data_frame.iterrows():
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