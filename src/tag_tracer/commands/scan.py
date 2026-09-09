import sys

from tag_tracer.browser.browser import BrowserManager
from tag_tracer.config.loader import ExcelConfig, ExcelLoader
from tag_tracer.network_capture.network_capture import NetworkCapture
from tag_tracer.reporting.console_report import (
    print_captured_requests,
    print_config_summary,
    print_final_status,
    print_header,
    print_validation_summary,
)
from tag_tracer.reporting.reporting import Reporting
from tag_tracer.validation.matcher import Matcher
from tag_tracer.validation.validation import Validator


def _resolve_scan_urls(url_arg: str, config: ExcelConfig) -> list[str]:
    """Resolves the --url argument into concrete URLs to scan.

    Passing 'all' (the default) scans every configured page's target URL;
    any other value is treated as a single URL.
    """
    if url_arg == "all":
        return [page.target_url for page in config.pages]
    return [url_arg]


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
        for url in _resolve_scan_urls(args.url, config_data):
            await browser_manager.navigate(url, settle_time=args.wait)

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

    except Exception as e:
        print(f"[TagTracer] Error during scan: {e}", file=sys.stderr)
        exit_code = 1
    finally:
        await browser_manager.close()
        print("\n[TagTracer] Scan complete.")
    return exit_code
