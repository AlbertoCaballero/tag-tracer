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

from src.commands.scan import scan
from src.commands.validate import validate
from src.commands.version import version


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

    # --------------------------------------------------------- scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a URL and capture marketing and analytics tags.",
    )
    scan_parser.add_argument(
        "--url",
        default="all",
        help="The URL to scan.",
    )
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

    # --------------------------------------------------------- validate command
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

    # --------------------------------------------------------- version command
    subparsers.add_parser(
        "version",
        help="Show TagTracer version information.",
    )

    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(scan(args))
        return

    if args.command == "validate":
        validate(args)
        return

    if args.command == "version":
        version()
        return

    # No command provided
    parser.print_help()


if __name__ == "__main__":
    main()
