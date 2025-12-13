"""
Validation module for TagTracer.
"""
from typing import List
from urllib.parse import urlparse, parse_qs
from tag_tracer.models import NetworkRequest
from tag_tracer.excel_loader.excel_loader import ExcelConfig

class Validator:
    def __init__(self, config: ExcelConfig):
        self.config = config

    def validate(self, requests: List[NetworkRequest]):
        print("\n[Validator] Starting validation...")
        matched_requests = 0
        for request in requests:
            for vendor_name, vendor_config in self.config.vendors.items():
                for domain in vendor_config.domains:
                    if domain in request.url:
                        print(f"\n[Validator] Matched request {request.url} to vendor {vendor_name}")
                        matched_requests += 1
                        
                        # Extract query parameters
                        parsed_url = urlparse(request.url)
                        query_params = parse_qs(parsed_url.query)
                        if query_params:
                            print(f"  [Validator] Found query parameters: {query_params}")

                        # Extract body parameters
                        if request.post_data:
                            body_params = parse_qs(request.post_data)
                            if body_params:
                                print(f"  [Validator] Found body parameters: {body_params}")

                        break
        
        print(f"\n[Validator] Validation complete. Matched {matched_requests} requests.")
