import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from src.validation.validation import ValidationSummary


def generate_html_report(summary: ValidationSummary, output_dir: str, filename: str = None):
    """
    Generates an HTML report from the validation summary using Jinja2.
    """
    os.makedirs(output_dir, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}.html"

    file_path = os.path.join(output_dir, filename)

    # Set up Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    # Render the template
    html_output = template.render(summary=summary, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(file_path, "w") as f:
        f.write(html_output)

    print(f"[Reporting] HTML report generated at: {file_path}")
