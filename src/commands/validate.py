import json
import sys
from typing_extensions import List
from src.config.loader import ExcelLoader
from src.models import NetworkRequest
from src.reporting.console_report import (
    print_final_status,
    print_header,
    print_validation_summary,
)
from src.reporting.reporting import Reporting
from src.validation.matcher import Matcher
from src.validation.validation import Validator


def validate(args):
    print_header(
        "TagTracer Validation",
        f"Input: {args.input} | Config: {args.config}",
    )

    # Load configuration
    try:
        loader = ExcelLoader(args.config)
        config_data = loader.load()
        print("[TagTracer] Configuration loaded successfully.")
    except Exception as e:
        print(f"[TagTracer] Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Load captured requests
    captured_requests: List[NetworkRequest] = []
    try:
        with open(args.input, "r") as f:
            raw_requests = json.load(f)
        captured_requests = [NetworkRequest(**req) for req in raw_requests]
        print(f"[TagTracer] Loaded {len(captured_requests)} requests.")
    except FileNotFoundError:
        print(
            f"[TagTracer] Error: Input file not found at {args.input}",
            file=sys.stderr,
        )
        sys.exit(1)
    except json.JSONDecodeError:
        print(
            f"[TagTracer] Error: Invalid JSON in input file {args.input}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"[TagTracer] Error loading captured requests: {e}", file=sys.stderr)
        sys.exit(1)

    # Perform validation
    matcher = Matcher()
    validator = Validator(config_data, matcher)
    validation_summary = validator.validate(captured_requests)
    print_validation_summary(validation_summary)
    print_final_status(validation_summary)

    # Generate reports
    reporting = Reporting(output_dir=args.output)
    report_formats = [f.strip() for f in args.report_formats.split(",")]
    reporting.generate_reports(validation_summary, report_formats)

    print("\n[TagTracer] Validation complete.")
    return 1 if validation_summary.pages_failed > 0 else 0