import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd

from tag_tracer.validation.validation import (
    ValidationSummary,
)

logger = logging.getLogger(__name__)


def generate_excel_report(
    summary: ValidationSummary, output_dir: str, filename: str = None
):
    """
    Generates an Excel report from the validation summary.
    """
    os.makedirs(output_dir, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}.xlsx"

    file_path = os.path.join(output_dir, filename)

    writer = pd.ExcelWriter(file_path, engine="openpyxl")

    # Summary Sheet
    summary_data = {
        "Metric": ["Total Pages Scanned", "Pages Passed", "Pages Failed"],
        "Value": [
            summary.total_pages_scanned,
            summary.pages_passed,
            summary.pages_failed,
        ],
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

    # Detailed Results Sheet
    all_results: list[dict[str, Any]] = []

    for page in summary.page_results:
        for request in page.request_results:
            for tag in request.tags_validated:
                all_results.append(
                    {
                        "Page ID": page.page_id,
                        "Page URL": page.page_url,
                        "Page Overall Status": page.overall_status,
                        "Request URL": request.request_url,
                        "Vendor Name": request.vendor_name,
                        "Request Overall Status": request.overall_status,
                        "Tag Key": tag.key,
                        "Field": tag.field,
                        "Location": tag.location,
                        "Expected Value": tag.expected_value,
                        "Actual Value": tag.actual_value,
                        "Rule Type": tag.rule_type,
                        "Case Sensitive": tag.case_sensitive,
                        "Tag Status": tag.status,
                        "Message": tag.message,
                    }
                )

    if all_results:
        details_df = pd.DataFrame(all_results)
        details_df.to_excel(writer, sheet_name="Detailed Results", index=False)
    else:
        # Create an empty DataFrame with headers if no results, to avoid error
        empty_df = pd.DataFrame(
            columns=[
                "Page ID",
                "Page URL",
                "Page Overall Status",
                "Request URL",
                "Vendor Name",
                "Request Overall Status",
                "Tag Key",
                "Field",
                "Location",
                "Expected Value",
                "Actual Value",
                "Rule Type",
                "Case Sensitive",
                "Tag Status",
                "Message",
            ]
        )
        empty_df.to_excel(writer, sheet_name="Detailed Results", index=False)

    writer.close()
    logger.info("Excel report generated at: %s", file_path)
