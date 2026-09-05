"""Network capture utilities for TagTracer.
Handles filtering and persistence of network requests.

"""

import json
import logging
import os

from tag_tracer.models import NetworkRequest
from tag_tracer.utils.utils import url_matches_domain

logger = logging.getLogger(__name__)


class NetworkCapture:
    def __init__(self, domain_filters: list[str] = None, output_dir: str = None):
        self.domain_filters = domain_filters or []
        self.output_dir = output_dir

    def filter_requests(self, requests: list[NetworkRequest]) -> list[NetworkRequest]:
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

    def save_requests_to_json(
        self, requests: list[NetworkRequest], filename: str = "captured_requests.json"
    ):
        if not self.output_dir:
            logger.warning("output_dir not set, skipping JSON save.")
            return

        os.makedirs(self.output_dir, exist_ok=True)
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, "w") as f:
            json.dump([req.model_dump() for req in requests], f, indent=4)
        logger.info("Saved %s requests to %s", len(requests), file_path)
