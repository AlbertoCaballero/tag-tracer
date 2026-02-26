"""Reporting module for TagTracer.
Responsible for aggregating validation results, generating reports,
and exporting findings to various formats (e.g., JSON, HTML, Excel).
"""

from typing import List

from src.reporting.excel_report import generate_excel_report
from src.reporting.html_report import generate_html_report
from src.reporting.json_report import generate_json_report
from src.validation.validation import ValidationSummary


class Reporting:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate_reports(self, summary: ValidationSummary, formats: List[str]):
        if "json" in formats:
            generate_json_report(summary, self.output_dir)
        if "html" in formats:
            generate_html_report(summary, self.output_dir)
        if "excel" in formats:
            # Requires openpyxl or xlsxwriter to be installed
            generate_excel_report(summary, self.output_dir)
