import logging
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from tag_tracer.validation.validation import ValidationSummary

logger = logging.getLogger(__name__)


def generate_html_report(
    summary: ValidationSummary, output_dir: str, filename: str = None
):
    """
    Generates an HTML report from the validation summary using Jinja2.
    """
    os.makedirs(output_dir, exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}.html"

    file_path = os.path.join(output_dir, filename)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("report_template.html")

    html_output = template.render(
        summary=summary,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    with open(file_path, "w") as f:
        f.write(html_output)

    logger.info("HTML report generated at: %s", file_path)
