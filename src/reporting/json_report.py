import json
import os
from datetime import datetime

from src.validation.validation import ValidationSummary


def generate_json_report(summary: ValidationSummary, output_dir: str, filename: str = None):
    """
    Generates a JSON report from the validation summary.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}.json"
    
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, "w") as f:
        json.dump(summary.dict(), f, indent=4)
        
    print(f"[Reporting] JSON report generated at: {file_path}")
