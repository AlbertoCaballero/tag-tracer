import json
import sys
from typing_extensions import List
from src.config.loader import ExcelLoader
from src.models import NetworkRequest
from src.reporting.reporting import Reporting
from src.validation.matcher import Matcher
from src.validation.validation import Validator


def validate(args):
    print(
        f"\n[TagTracer] Validation requested for input: {args.input} with config: {args.config}"
    )

    # Load configuration
    try:
        print(f"[TagTracer] Loading configuration from: {args.config}")
        loader = ExcelLoader(args.config)
        config_data = loader.load()
        print("[TagTracer] Configuration loaded successfully.")
    except Exception as e:
        print(f"[TagTracer] Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Load captured requests
    captured_requests: List[NetworkRequest] = []
    try:
        print(f"[TagTracer] Loading captured requests from: {args.input}")
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

    print("\n--- Validation Summary ---")
    print(f"Total Pages Scanned: {validation_summary.total_pages_scanned}")
    print(f"Pages Passed: {validation_summary.pages_passed}")
    print(f"Pages Failed: {validation_summary.pages_failed}")
    for page_result in validation_summary.page_results:
        print(
            f"  Page '{page_result.page_id}' ({page_result.page_url}): {page_result.overall_status}"
        )
        for req_result in page_result.request_results:
            print(
                f"    Request to '{req_result.request_url}' ({req_result.vendor_name}): {req_result.overall_status}"
            )
            for tag_result in req_result.tags_validated:
                print(
                    f"      Tag '{tag_result.key}': {tag_result.status} - {tag_result.message}"
                )

    # Generate reports
    reporting = Reporting(output_dir=args.output)
    report_formats = [f.strip() for f in args.report_formats.split(",")]
    reporting.generate_reports(validation_summary, report_formats)

    print("[TagTracer] Validation complete.")
