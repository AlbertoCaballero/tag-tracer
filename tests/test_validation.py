import pytest
from src.validation.validation import (
    Validator,
    ValidationSummary,
    PageValidationResult,
    RequestValidationResult,
    TagValidationResult,
)
from src.validation.matcher import Matcher
from src.validation.rules import ExpectedTag, ValidationRule
from src.models import NetworkRequest
from src.config.loader import ExcelConfig, VendorConfig, PageConfig

@pytest.fixture
def sample_matcher():
    return Matcher()

@pytest.fixture
def sample_excel_config():
    return ExcelConfig(
        vendors={
            "analytics": VendorConfig(domains=["google-analytics.com", "googletagmanager.com"]),
            "marketing": VendorConfig(domains=["ads.example.com"]),
        },
        pages=[
            PageConfig(
                id="home_page",
                target_url="http://localhost:8000/",
                page_vendors=["analytics"],
                expected_tags={
                    "event": "page_view", # Primitive value
                    "page_location": {"value": "http://localhost:8000/", "rules": {"exact_match": {"type": "exact", "value": "http://localhost:8000/"}}}, # Dictionary with value and rules
                    "campaign_id": {"rules": {"regex_match": {"type": "regex", "value": r"^CID-\d+"}}}, # Dictionary with rules only
                    "user_id": {"rules": {"present_check": {"type": "present"}}}, # Dictionary with rules only
                    "optional_param": {"value": "some_value", "rules": {"contains_check": {"type": "contains", "value": "some"}}} # Dictionary with value and rules
                },
            ),
            PageConfig(
                id="product_page",
                target_url="http://localhost:8000/product/123",
                page_vendors=["analytics", "marketing"],
                expected_tags={
                    "event": "view_item",
                    "item_id": {"value": "123", "rules": {"exact": {"type": "exact", "value": "123"}}},
                },
            ),
        ],
    )

@pytest.fixture
def sample_network_requests():
    return [
        NetworkRequest(
            url="http://google-analytics.com/collect?v=1&_v=j88&tid=UA-XXXXX-Y&cid=123.456&t=pageview&dl=http%3A%2F%2Flocalhost%3A8000%2F&dt=Home&ev=page_view",
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest(
            url="http://google-analytics.com/collect?v=1&_v=j88&tid=UA-XXXXX-Y&cid=123.456&t=event&dl=http%3A%2F%2Flocalhost%3A8000%2Fproduct%2F123&ev=view_item&item_id=123",
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest(
            url="http://ads.example.com/track?id=abc&campaign_id=CID-987",
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest( # Irrelevant request
            url="http://some-other-domain.com/data",
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest( # For home_page, user_id present
            url="http://google-analytics.com/collect?v=1&user_id=12345&ev=page_view&dl=http%3A%2F%2Flocalhost%3A8000%2F",
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest( # For home_page, optional_param contains "some"
            url="http://google-analytics.com/collect?v=1&optional_param=some_value_here&ev=page_view&dl=http%3A%2F%2Flocalhost%3A8000%2F",
            method="GET",
            headers={},
            post_data=None,
        ),
    ]

def test_validator_initialization(sample_excel_config, sample_matcher):
    validator = Validator(sample_excel_config, sample_matcher)
    assert validator.config == sample_excel_config
    assert validator.matcher == sample_matcher

def test_get_relevant_requests(sample_excel_config, sample_matcher, sample_network_requests):
    validator = Validator(sample_excel_config, sample_matcher)
    
    # Test for home_page vendors (analytics)
    relevant = validator._get_relevant_requests(sample_network_requests, ["analytics"])
    assert len(relevant) == 4 # GA page_view (home), GA view_item (product), GA user_id, GA optional_param

    # Test for product_page vendors (analytics, marketing)
    relevant = validator._get_relevant_requests(sample_network_requests, ["analytics", "marketing"])
    assert len(relevant) == 5 # GA page_view (home), GA view_item (product), Ads track, GA user_id, GA optional_param

def test_validate_home_page_all_passed(sample_excel_config, sample_matcher):
    validator = Validator(sample_excel_config, sample_matcher)
    
    # Simulate a single request that has all expected tags for the home page
    requests_for_home = [
        NetworkRequest(
            url="http://google-analytics.com/collect?v=1&_v=j88&tid=UA-XXXXX-Y&cid=123.456&t=pageview&dl=http%3A%2F%2Flocalhost%3A8000%2F&dt=Home&event=page_view&page_location=http%3A%2F%2Flocalhost%3A8000%2F&user_id=ABC&campaign_id=CID-123&optional_param=some_value_here",
            method="GET",
            headers={},
            post_data=None,
        ),
    ]

    summary = validator.validate(requests_for_home)

    assert isinstance(summary, ValidationSummary)
    assert summary.total_pages_scanned == 2 # All pages in config
    assert summary.pages_passed == 1 # Only home_page should pass if other pages have no relevant requests
    assert summary.pages_failed == 1

    home_page_result = next((p for p in summary.page_results if p.page_id == "home_page"), None)
    assert home_page_result is not None
    assert home_page_result.overall_status == "passed"
    assert home_page_result.expected_tags_count == 5
    assert home_page_result.matched_requests_count == 1 # Now only 1 request
    assert len(home_page_result.request_results) == 1

    # Check tags for the single request
    req_results = home_page_result.request_results[0].tags_validated
    assert all(tag.status == "passed" for tag in req_results)

    event_tag = next(t for t in req_results if t.key == "event")
    assert event_tag.status == "passed"
    assert event_tag.actual_value == "page_view"

    page_location_tag = next(t for t in req_results if t.key == "page_location")
    assert page_location_tag.status == "passed"
    assert page_location_tag.actual_value == "http://localhost:8000/"

    campaign_id_tag = next(t for t in req_results if t.key == "campaign_id")
    assert campaign_id_tag.status == "passed"
    assert campaign_id_tag.actual_value == "CID-123"

    user_id_tag = next(t for t in req_results if t.key == "user_id")
    assert user_id_tag.status == "passed"
    assert user_id_tag.actual_value == "ABC"

    optional_param_tag = next(t for t in req_results if t.key == "optional_param")
    assert optional_param_tag.status == "passed"
    assert optional_param_tag.actual_value == "some_value_here"

def test_validate_home_page_some_failed(sample_excel_config, sample_matcher):
    validator = Validator(sample_excel_config, sample_matcher)
    
    requests_for_home_failed = [
        NetworkRequest(
            url="http://google-analytics.com/collect?v=1&_v=j88&tid=UA-XXXXX-Y&cid=123.456&t=pageview&dl=http%3A%2F%2Flocalhost%3A8000%2F&dt=Home&event=wrong_value&page_location=http%3A%2F%2Fwrong.com%2F", # Incorrect values
            method="GET",
            headers={},
            post_data=None,
        ),
        NetworkRequest( # Missing user_id
            url="http://google-analytics.com/collect?v=1&event=page_view&page_location=http%3A%2F%2Flocalhost%3A8000%2F",
            method="GET",
            headers={},
            post_data=None,
        ),
    ]

    summary = validator.validate(requests_for_home_failed)

    home_page_result = next((p for p in summary.page_results if p.page_id == "home_page"), None)
    assert home_page_result.overall_status == "failed"

    # Check first request's tags
    req1_results = home_page_result.request_results[0].tags_validated
    event_tag = next(t for t in req1_results if t.key == "event")
    assert event_tag.status == "failed"
    assert event_tag.actual_value == "wrong_value"

    page_location_tag = next(t for t in req1_results if t.key == "page_location")
    assert page_location_tag.status == "failed"
    assert page_location_tag.actual_value == "http://wrong.com/"

    # Check second request's tags (user_id missing)
    req2_results = home_page_result.request_results[1].tags_validated
    user_id_tag = next(t for t in req2_results if t.key == "user_id")
    assert user_id_tag.status == "failed"
    assert user_id_tag.actual_value is None
