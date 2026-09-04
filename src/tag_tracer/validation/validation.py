"""
Validation module for TagTracer.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel

from tag_tracer.config.loader import ExcelConfig, PageConfig
from tag_tracer.models import NetworkRequest
from tag_tracer.utils.utils import url_matches_domain
from tag_tracer.validation.matcher import Matcher
from tag_tracer.validation.rules import ExpectedTag, ValidationRule


class TagValidationResult(BaseModel):
    key: str
    field: str = ""
    location: str = ""
    expected_value: Any
    actual_value: Any
    rule_type: str
    case_sensitive: bool
    status: str
    message: str


class RequestValidationResult(BaseModel):
    request_url: str
    method: str = ""
    vendor_name: str
    matched_domains: List[str]
    query_params: Dict[str, Any] = {}
    body_params: Dict[str, Any] = {}
    header_params: Dict[str, Any] = {}
    tags_validated: List[TagValidationResult]
    overall_status: str


class PageValidationResult(BaseModel):
    page_id: str
    page_url: str
    expected_tags_count: int
    matched_requests_count: int
    expected_tags: Dict[str, Any] = {}
    found_tags: Dict[str, Any] = {}
    expected_tag_status: List[Dict[str, Any]] = []
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
                    if any(
                        url_matches_domain(req_url, domain)
                        for domain in v_config.domains
                    ):
                        vendor_name = v_name
                        matched_domains = [
                            d for d in v_config.domains if url_matches_domain(req_url, d)
                        ]
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
                body_params = self._parse_body_params(req.post_data)
                header_params = self._normalize_headers(req.headers or {})

                # Validate expected tags for this page, scoped to the request's vendor
                for expected_tag_key, expected_tag_value in page.expected_tags.items():
                    owning_vendor, param_name = self._resolve_tag_key(
                        expected_tag_key, page.page_vendors
                    )
                    # Skip tags that belong to a different vendor
                    if owning_vendor and owning_vendor != vendor_name:
                        continue

                    # The value from page.expected_tags can be a primitive or a dictionary
                    # We need to construct an ExpectedTag instance from it
                    if isinstance(expected_tag_value, dict):
                        # If it's already a dict, assume it contains explicit rules/value
                        tag_data = expected_tag_value
                    else:
                        # If it's a primitive, assume it implies an exact match
                        tag_data = {"value": expected_tag_value}

                    # The ExpectedTag key is the actual parameter name used for lookup
                    expected_tag = ExpectedTag(key=param_name, **tag_data)

                    # Resolve where the field should live from the owning vendor's config
                    field_locations = self._field_locations(owning_vendor or vendor_name)
                    actual_value, source = self._lookup_value(
                        param_name, field_locations, query_params, body_params, header_params
                    )
                    location = source or field_locations.get(param_name) or "N/A"

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
                            key=expected_tag_key,
                            field=param_name,
                            location=location,
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
                        method=req.method,
                        vendor_name=vendor_name,
                        matched_domains=matched_domains,
                        query_params=query_params,
                        body_params=body_params,
                        header_params=header_params,
                        tags_validated=tags_validated,
                        overall_status=request_overall_status,
                    )
                )

            # Determine page overall status: every expected tag must have
            # passed on at least one request (missing tags => fail).
            passed_tag_keys = {
                tag_res.key
                for req_res in page_matched_requests
                for tag_res in req_res.tags_validated
                if tag_res.status == "passed"
            }
            if page_matched_requests and all(
                tag_key in passed_tag_keys for tag_key in page.expected_tags.keys()
            ):
                page_overall_status = "passed"
                pages_passed += 1

            # Aggregate every parameter actually found across the page's requests
            found_tags: Dict[str, Any] = {}
            for req_res in page_matched_requests:
                found_tags.update(req_res.query_params)
                found_tags.update(req_res.body_params)

            # Resolve each expected tag to its field/location and mark found/missing.
            # Derive from the per-request validation results (vendor-scoped and
            # correct) instead of re-aggregating raw params across all vendors.
            expected_tag_status: List[Dict[str, Any]] = []
            tag_results: Dict[str, List[TagValidationResult]] = {}
            for req_res in page_matched_requests:
                for tag_res in req_res.tags_validated:
                    tag_results.setdefault(tag_res.key, []).append(tag_res)

            for tag_key, tag_value in page.expected_tags.items():
                owning_vendor, field = self._resolve_tag_key(tag_key, page.page_vendors)
                results = tag_results.get(tag_key, [])
                passed = [r for r in results if r.status == "passed"]

                if passed:
                    actual_value = passed[0].actual_value
                    location = passed[0].location
                    found = True
                elif results:
                    actual_value = results[0].actual_value
                    location = results[0].location
                    found = actual_value is not None
                else:
                    actual_value = None
                    location = "N/A"
                    found = False

                expected_tag_status.append(
                    {
                        "key": tag_key,
                        "vendor": owning_vendor or "",
                        "field": field,
                        "location": location,
                        "expected_value": tag_value,
                        "actual_value": actual_value,
                        "found": found,
                    }
                )

            page_results.append(
                PageValidationResult(
                    page_id=page.id,
                    page_url=page.target_url,
                    expected_tags_count=len(page.expected_tags),
                    matched_requests_count=matched_requests_count,
                    expected_tags=page.expected_tags,
                    found_tags=found_tags,
                    expected_tag_status=expected_tag_status,
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

    @staticmethod
    def _flatten_json(obj: Dict[str, Any], prefix: str = "", result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Flattens a nested JSON object into dotted paths, e.g.
        {'data': {'field': 'x'}} -> {'data.field': 'x'}.
        """
        if result is None:
            result = {}
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                Validator._flatten_json(value, full_key, result)
            elif isinstance(value, list):
                result[full_key] = json.dumps(value)
            else:
                result[full_key] = value
        return result

    @staticmethod
    def _parse_body_params(post_data: Optional[str]) -> Dict[str, Any]:
        """
        Parses a request body into a flat dict of parameters.
        Supports form-encoded and JSON bodies; nested JSON objects are
        flattened into dotted paths (e.g. {'data': {'field': 'x'}} -> {'data.field': 'x'}).
        """
        if not post_data:
            return {}
        stripped = post_data.strip()
        if stripped.startswith(("{", "[")):
            try:
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    return Validator._flatten_json(payload)
                return {}
            except (json.JSONDecodeError, ValueError):
                pass
        try:
            return {k: v[0] for k, v in parse_qs(post_data).items()}
        except Exception:
            return {}

    @staticmethod
    def _normalize_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes header keys to lowercase (HTTP headers are case-insensitive)."""
        return {str(k).lower(): v for k, v in headers.items()}

    def _field_locations(self, vendor_name: Optional[str]) -> Dict[str, str]:
        """
        Builds a map of field name -> parameter location ('query' | 'body' | 'header')
        from a vendor's declared query/body/header fields.
        """
        config = self.config.vendors.get(vendor_name or "")
        if not config:
            return {}
        locations: Dict[str, str] = {}
        for field in config.query_fields:
            locations[field] = "query"
        for field in config.body_fields:
            locations[field] = "body"
        for field in config.header_fields:
            locations[field] = "header"
        return locations

    @staticmethod
    def _lookup_value(
        field: str,
        field_locations: Dict[str, str],
        query_params: Dict[str, Any],
        body_params: Dict[str, Any],
        header_params: Dict[str, Any],
    ) -> tuple:
        """
        Returns (value, location) for a field. The declared location from the
        vendor config is checked first; if the field is not found there, all
        sources are searched (query -> body -> header) so that real beacons
        that differ from the config declaration are still matched.
        """
        declared = field_locations.get(field)
        if declared == "query":
            value = query_params.get(field)
            if value is not None:
                return value, "query"
        elif declared == "body":
            value = body_params.get(field)
            if value is not None:
                return value, "body"
        elif declared == "header":
            value = header_params.get(field.lower())
            if value is not None:
                return value, "header"

        for loc, params in (
            ("query", query_params),
            ("body", body_params),
            ("header", header_params),
        ):
            value = params.get(field.lower() if loc == "header" else field)
            if value is not None:
                return value, loc
        return None, None

    @staticmethod
    def _resolve_tag_key(key: str, page_vendors: List[str]):
        """
        Resolves an expected tag key into (owning_vendor, parameter_name).

        Keys may be prefixed with a vendor name (e.g. 'meta-ev' for vendor
        'meta' and parameter 'ev') to scope a tag to a specific vendor.
        Unprefixed keys are treated as global and apply to every request.
        """
        for vendor in page_vendors:
            prefix = f"{vendor}-"
            if key.startswith(prefix):
                return vendor, key[len(prefix):]
        return None, key

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
            if any(
                url_matches_domain(req.url, domain)
                for domain in vendor_domains_for_page
            ):
                relevant_requests.append(req)
        return relevant_requests
