from typing import Any

import pandas as pd
from pydantic import BaseModel

from tag_tracer.utils.utils import string_to_list


class VendorConfig(BaseModel):
    domains: list[str] = []
    query_fields: list[str] = []
    body_fields: list[str] = []
    header_fields: list[str] = []


class PageConfig(BaseModel):
    id: str
    target_url: str
    page_vendors: list[str] = []
    expected_tags: dict[str, Any] = {}


class ExcelConfig(BaseModel):
    vendors: dict[str, VendorConfig] = {}
    pages: list[PageConfig] = []


class ExcelLoader:
    def __init__(self, path: str):
        self.path = path
        try:
            self.workbook = pd.ExcelFile(path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file not found at: {path}") from e

    def load(self) -> ExcelConfig:
        config = ExcelConfig()

        for sheet_name in self.workbook.sheet_names:
            data_frame = self.workbook.parse(sheet_name).dropna(how="all")
            if sheet_name == "pages":
                for _, row in data_frame.iterrows():
                    page = PageConfig(
                        id=row["id"],
                        target_url=row["target-url"],
                        page_vendors=string_to_list(row["vendors"]),
                    )
                    for col in data_frame.columns:
                        if col not in ["id", "target-url", "vendors"]:
                            if pd.notna(row[col]):
                                page.expected_tags[col] = row[col]
                    config.pages.append(page)
            else:  # Vendor sheets
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

                    if key == "domain":
                        vendor_config.domains.append(value)
                    elif key == "query-fields":
                        vendor_config.query_fields.extend(string_to_list(value))
                    elif key == "body-field" or key == "body-fields":
                        vendor_config.body_fields.extend(string_to_list(value))
                    elif key == "header-fields":
                        vendor_config.header_fields.extend(string_to_list(value))

                config.vendors[vendor_name] = vendor_config

        return config
