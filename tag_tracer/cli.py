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
import sys

from tag_tracer.excel_loader.excel_loader import ExcelLoader
from tag_tracer.utils.utils import format_expected_tags

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
        help="Optional path to a configuration file (Excel/YAML).",
    )

    # TODO: Implement scan execution handler

    # ---------------------------------------------------------
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate captured tag data against configured rules.",
    )
    validate_parser.add_argument(
        "--input",
        help="Path to a previously captured network log file.",
    )

    # TODO: Implement validation handler

    # ---------------------------------------------------------
    # version command
    subparsers.add_parser(
        "version",
        help="Show TagTracer version information.",
    )

    # ---------------------------------------------------------

    args = parser.parse_args()

    if args.command == "scan":
        import asyncio
        from tag_tracer.browser.browser import BrowserManager

        async def run_scan():
            print(f"[TagTracer] Scan requested for URL: {args.url}")
            if args.config:
                try:
                    print(f"[TagTracer] Loading configuration from: {args.config}")
                    loader = ExcelLoader(args.config)
                    config_data = loader.load()
                    print("[TagTracer] Configuration loaded successfully.")
                    print("\n--- Vendors ---")
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

                    print("\n--- Pages ---")
                    for page in config_data.pages:
                        print(f"  - Page ID: {page.id}")
                        print(f"    URL: {page.target_url}")
                        print(f"    Expected Tags: ")
                        format_expected_tags(page.expected_tags)
                except Exception as e:
                    print(f"[TagTracer] Error loading configuration: {e}", file=sys.stderr)
                    sys.exit(1)

            browser_manager = BrowserManager(headless=True)
            try:
                await browser_manager.launch()
                await browser_manager.navigate(args.url)
                
                requests = browser_manager.get_captured_requests()
                print(f"\n[TagTracer] Captured {len(requests)} network requests.")
                for i, req in enumerate(requests[:5]):
                    print(f"  - Req {i+1}: {req.method} {req.url}")

                if args.config:
                    from tag_tracer.validation.validation import Validator
                    validator = Validator(config_data)
                    validator.validate(requests)
            finally:
                await browser_manager.close()
                print("[TagTracer] Scan complete.")

        asyncio.run(run_scan())
        return

    if args.command == "validate":
        # TODO: Integrate with validation engine
        print(f"[TagTracer] Validation requested for file: {args.input}")
        return

    if args.command == "version":
        print("TagTracer version 0.1.0 (development preview)")
        return

    # No command provided
    parser.print_help()


if __name__ == "__main__":
    main()

