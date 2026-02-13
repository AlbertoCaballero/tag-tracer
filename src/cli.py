#!/usr/bin/env python3
"""
TagTracer CLI Module
---------------------

This module serves as the primary entry point for the TagTracer command-line
interface. It provides the command router, high-level descriptions, and the
initial scaffolding for future functional components such as scanning,
validation, configuration loading, and reporting.

All operational logic will be implemented in the appropriate modules within
the tag_tracer package. This file should remain focused solely on CLI
parsing, dispatching, and presentation.
"""

import argparse
import asyncio
import json
import sys
from typing import List

from src.browser.browser import BrowserManager
from src.config.loader import ExcelLoader
from src.models import NetworkRequest  # New import
from src.network_capture.network_capture import NetworkCapture
from src.reporting.reporting import Reporting
from src.utils.utils import format_expected_tags  # Updated import
from src.validation.matcher import Matcher
from src.validation.validation import Validator


def main():
    parser = argparse.ArgumentParser(
        prog="tag-tracer",
        description=(
            "TagTracer – Automated marketing and analytics tag tracing tool. "
            "Captures network calls from a headless browser and validates them "
            "against configurable rules defined in Excel or YAML."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ---------------------------------------------------------
    # scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a URL and capture marketing and analytics tags.",
    )
    scan_parser.add_argument("url", help="The URL to scan.")
    scan_parser.add_argument(
        "--config",
        required=True,  # Config is now required for scan
        help="Path to the configuration file (Excel).",
    )
    scan_parser.add_argument(
        "--output",
        default="output",
        help="Directory to save captured network requests and reports.",
    )
    scan_parser.add_argument(
        "--report-formats",
        default="json,html",
        help="Comma-separated list of report formats to generate (json, html, excel).",
    )

    # ---------------------------------------------------------
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate previously captured tag data against configured rules.",
    )
    validate_parser.add_argument(
        "--input",
        required=True,
        help="Path to a previously captured network log file (JSON).",
    )
    validate_parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration file (Excel).",
    )
    validate_parser.add_argument(
        "--output",
        default="output",
        help="Directory to save generated reports.",
    )
    validate_parser.add_argument(
        "--report-formats",
        default="json,html",
        help="Comma-separated list of report formats to generate (json, html, excel).",
    )

    # ---------------------------------------------------------
    # version command
    subparsers.add_parser(
        "version",
        help="Show TagTracer version information.",
    )

    # ---------------------------------------------------------

    args = parser.parse_args()

    if args.command == "scan":

        async def run_scan():
            print(f"\n[TagTracer] Scan requested for URL: {args.url}")
            loader = ExcelLoader(args.config)
            config_data = loader.load()
            if args.config:
                try:
                    print(f"[TagTracer] Loading configuration from: {args.config}")
                    print("[TagTracer] Configuration loaded successfully.")
                    print("\n[Vendors]")
                    for vendor_name, vendor_config in config_data.vendors.items():
                        print(f"  - {vendor_name}:")
                        if vendor_config.domains:
                            print(f"    Domains: {vendor_config.domains}")
                        if vendor_config.query_fields:
                            print(f"    Query Fields: {vendor_config.query_fields}")
                        if vendor_config.body_fields:
                            print(f"    Body Fields: {vendor_config.body_fields}")
                        if vendor_config.header_fields:
                            print(f"    Header Fields: {vendor_config.header_fields}")

                    print("\n[Pages]")
                    for page in config_data.pages:
                        print(f"    ID: {page.id}")
                        print(f"    URL: {page.target_url}")
                        print("    Expected Tags:")
                        print(format_expected_tags(page.expected_tags))  # Updated call
                except Exception as e:
                    print(
                        f"[TagTracer] Error loading configuration: {e}", file=sys.stderr
                    )
                    sys.exit(1)

            browser_manager = BrowserManager(headless=True)
            try:
                await browser_manager.launch()
                await browser_manager.navigate(args.url)

                requests = browser_manager.get_captured_requests()
                print(f"\n[TagTracer] Captured {len(requests)} network requests.")
                for i, req in enumerate(requests[:5]):
                    print(f"  - Req {i + 1}: {req.method} {req.url}")

                if config_data:
                    vendor_domains = []
                    for vendor_config in config_data.vendors.values():
                        vendor_domains.extend(vendor_config.domains)

                    network_capture = NetworkCapture(
                        domain_filters=vendor_domains, output_dir=args.output
                    )
                    filtered_requests = network_capture.filter_requests(requests)
                    network_capture.save_requests_to_json(
                        filtered_requests, filename="captured_filtered_requests.json"
                    )

                    matcher = Matcher()
                    validator = Validator(config_data, matcher)
                    validation_summary = validator.validate(filtered_requests)

                    print("\n--- Validation Summary ---")
                    print(
                        f"Total Pages Scanned: {validation_summary.total_pages_scanned}"
                    )
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

            finally:
                await browser_manager.close()
                print("[TagTracer] Scan complete.")

        asyncio.run(run_scan())
        return

    if args.command == "validate":
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
        return

    if args.command == "version":
        print("TagTracer version 0.1.0 (development preview)")
        return

    # No command provided
    parser.print_help()


if __name__ == "__main__":
    main()
