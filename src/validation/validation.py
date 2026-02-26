"""
Validation module for TagTracer.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel

from src.config.loader import ExcelConfig, PageConfig
from src.models import NetworkRequest
from src.validation.matcher import Matcher
from src.validation.rules import ExpectedTag, ValidationRule


class TagValidationResult(BaseModel):
    key: str
    expected_value: Any
    actual_value: Any
    rule_type: str
    case_sensitive: bool
    status: str
    message: str


class RequestValidationResult(BaseModel):
    request_url: str
    vendor_name: str
    matched_domains: List[str]
    tags_validated: List[TagValidationResult]
    overall_status: str


class PageValidationResult(BaseModel):
    page_id: str
    page_url: str
    expected_tags_count: int
    matched_requests_count: int
    request_results: List[RequestValidationResult]
    overall_status: str


class ValidationSummary(BaseModel):
    total_pages_scanned: int
    pages_passed: int
    pages_failed: int
    page_results: List[PageValidationResult]


class Validator:
    def __init__(self, config: ExcelConfig, matcher: Matcher):
        self.config = config
        self.matcher = matcher

    def validate(self, captured_requests: List[NetworkRequest]) -> ValidationSummary:
        print("\n[Validator] Starting validation...")
        page_results: List[PageValidationResult] = []
        total_pages_scanned = len(self.config.pages)
        pages_passed = 0

        for page in self.config.pages:
            page_matched_requests: List[RequestValidationResult] = []
            page_overall_status = "failed"  # Assume failed until all pass
            matched_requests_count = 0

            # Find requests relevant to this page's vendors
            relevant_requests = self._get_relevant_requests(
                captured_requests, page.page_vendors
            )

            for req in relevant_requests:
                req_url = req.url
                vendor_name = ""  # Determine vendor name
                matched_domains: List[str] = []

                # Determine which vendor this request belongs to
                for v_name, v_config in self.config.vendors.items():
                    if any(domain in req_url for domain in v_config.domains):
                        vendor_name = v_name
                        matched_domains = [d for d in v_config.domains if d in req_url]
                        break

                if not vendor_name:
                    # This should ideally not happen if _get_relevant_requests is effective
                    continue

                matched_requests_count += 1
                tags_validated: List[TagValidationResult] = []
                request_overall_status = "passed"

                # Extract parameters from request
                parsed_url = urlparse(req_url)
                query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
                body_params = {}
                if req.post_data:
                    # Assuming JSON or form-encoded; simple parse_qs for now
                    try:
                        # Attempt to parse as form-encoded
                        body_params = {
                            k: v[0] for k, v in parse_qs(req.post_data).items()
                        }
                    except Exception:
                        pass  # Could be JSON, not handled by parse_qs

                all_params = {**query_params, **body_params}

                # Validate expected tags for this page
                for expected_tag_key, expected_tag_value in page.expected_tags.items():
                    # The value from page.expected_tags can be a primitive or a dictionary
                    # We need to construct an ExpectedTag instance from it
                    
                    if isinstance(expected_tag_value, dict):
                        # If it's already a dict, assume it contains explicit rules/value
                        tag_data = expected_tag_value
                    else:
                        # If it's a primitive, assume it implies an exact match
                        tag_data = {"value": expected_tag_value}
                    
                    # Always provide the key explicitly
                    expected_tag = ExpectedTag(key=expected_tag_key, **tag_data)
    
                    actual_value = all_params.get(expected_tag.key)
                    tag_status = "failed"
                    tag_message = "No matching rule passed"

                    rule_passed = False
                    for rule_name, rule in expected_tag.rules.items():
                        is_match = self.matcher.match(rule, actual_value)
                        if is_match:
                            rule_passed = True
                            tag_status = "passed"
                            tag_message = f"Matched by rule '{rule_name}'"
                            break  # First rule to pass is enough

                    if not rule_passed:
                        request_overall_status = "failed"

                    tags_validated.append(
                        TagValidationResult(
                            key=expected_tag.key,
                            expected_value=rule.value if rule_passed and rule.value is not None else expected_tag.value,
                            actual_value=actual_value,
                            rule_type=rule.type if rule_passed else "N/A",
                            case_sensitive=rule.case_sensitive if rule_passed else True,
                            status=tag_status,
                            message=tag_message,
                        )
                    )

                page_matched_requests.append(
                    RequestValidationResult(
                        request_url=req_url,
                        vendor_name=vendor_name,
                        matched_domains=matched_domains,
                        tags_validated=tags_validated,
                        overall_status=request_overall_status,
                    )
                )

            # Determine page overall status
            if all(
                req_res.overall_status == "passed" for req_res in page_matched_requests
            ):
                page_overall_status = "passed"
                pages_passed += 1

            page_results.append(
                PageValidationResult(
                    page_id=page.id,
                    page_url=page.target_url,
                    expected_tags_count=len(page.expected_tags),
                    matched_requests_count=matched_requests_count,
                    request_results=page_matched_requests,
                    overall_status=page_overall_status,
                )
            )

        summary = ValidationSummary(
            total_pages_scanned=total_pages_scanned,
            pages_passed=pages_passed,
            pages_failed=total_pages_scanned - pages_passed,
            page_results=page_results,
        )
        print(
            f"\n[Validator] Validation complete. Pages passed: {pages_passed}/{total_pages_scanned}"
        )
        return summary

    def _get_relevant_requests(
        self, captured_requests: List[NetworkRequest], page_vendors: List[str]
    ) -> List[NetworkRequest]:
        """
        Filters captured requests to only include those from vendors specified for the current page.
        """
        relevant_requests = []
        vendor_domains_for_page = set()
        for vendor_name in page_vendors:
            vendor_config = self.config.vendors.get(vendor_name)
            if vendor_config:
                vendor_domains_for_page.update(vendor_config.domains)

        for req in captured_requests:
            if any(domain in req.url for domain in vendor_domains_for_page):
                relevant_requests.append(req)
        return relevant_requests
