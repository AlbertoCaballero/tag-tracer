"""Network capture utilities for TagTracer.
Handles filtering and persistence of network requests.

"""

import json
from typing import List

from src.models import NetworkRequest
from src.utils.utils import url_matches_domain


class NetworkCapture:
    def __init__(self, domain_filters: List[str] = None, output_dir: str = None):
        self.domain_filters = domain_filters or []
        self.output_dir = output_dir

    def filter_requests(self, requests: List[NetworkRequest]) -> List[NetworkRequest]:
        if not self.domain_filters:
            return requests

        return [
            request
            for request in requests
            if any(
                url_matches_domain(request.url, domain)
                for domain in self.domain_filters
            )
        ]

    def save_requests_to_json(self, requests: List[NetworkRequest], filename: str = "captured_requests.json"):
        if not self.output_dir:
            print("[NetworkCapture] Warning: output_dir not set, skipping JSON save.")
            return

        import os

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, "w") as f:
            json.dump([req.dict() for req in requests], f, indent=4)
        print(f"[NetworkCapture] Saved {len(requests)} requests to {file_path}")
