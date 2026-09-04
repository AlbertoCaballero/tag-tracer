import sys
from src.browser.browser import BrowserManager
from src.config.loader import ExcelLoader
from src.network_capture.network_capture import NetworkCapture
from src.reporting.console_report import (
    print_captured_requests,
    print_config_summary,
    print_final_status,
    print_header,
    print_validation_summary,
)
from src.reporting.reporting import Reporting
from src.validation.matcher import Matcher
from src.validation.validation import Validator


async def scan(args):
    print_header(
        "TagTracer Scan",
        f"URL: {args.url}",
    )

    try:
        loader = ExcelLoader(args.config)
        config_data = loader.load()
        print_config_summary(config_data)
    except Exception as e:
        print(f"[TagTracer] Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    browser_manager = BrowserManager(headless=args.headless)
    exit_code = 0
    try:
        await browser_manager.launch()
        await browser_manager.navigate(args.url, settle_time=args.wait)

        requests = browser_manager.get_captured_requests()
        print_captured_requests(requests)

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
            print_validation_summary(validation_summary)
            print_final_status(validation_summary)
            if validation_summary.pages_failed > 0:
                exit_code = 1

            # Generate reports
            reporting = Reporting(output_dir=args.output)
            report_formats = [f.strip() for f in args.report_formats.split(",")]
            reporting.generate_reports(validation_summary, report_formats)

    finally:
        await browser_manager.close()
        print("\n[TagTracer] Scan complete.")
    return exit_code