import sys
from src.browser.browser import BrowserManager
from src.config.loader import ExcelLoader
from src.network_capture.network_capture import NetworkCapture
from src.reporting.reporting import Reporting
from src.utils.utils import print_expected_tags
from src.validation.matcher import Matcher
from src.validation.validation import Validator


async def scan(args):
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
                print_expected_tags(page.expected_tags)
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
        for i, req in enumerate(requests):
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
