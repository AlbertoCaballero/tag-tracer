import pytest

from tag_tracer.models import NetworkRequest
from tag_tracer.network_capture.network_capture import NetworkCapture
from tag_tracer.utils.utils import url_matches_domain


def _req(url):
    return NetworkRequest(url=url, method="GET", headers={}, post_data=None)


@pytest.mark.parametrize(
    "url, domain, expected",
    [
        ("https://www.facebook.com/tr/?ev=1", "www.facebook.com", True),
        ("https://www.facebook.com/tr/?ev=1", "facebook.com", True),
        ("https://facebook.com/tr/?ev=1", "facebook.com", True),
        ("https://www.notfacebook.com/tr/?ev=1", "facebook.com", False),
        ("https://notexample.com/x", "example.com", False),
        ("https://example.com/x", "example.com", True),
        ("https://sub.doubleclick.net/x", "doubleclick.net", True),
        ("http://localhost:8999/", "localhost", True),
        ("https://www.FACEBOOK.com/x", "www.facebook.com", True),
        ("https://www.facebook.com/x", " www.facebook.com ", True),
    ],
)
def test_url_matches_domain(url, domain, expected):
    assert url_matches_domain(url, domain) is expected


def test_filter_requests_matches_hostname():
    capture = NetworkCapture(domain_filters=["facebook.com", "doubleclick.net"])
    requests = [
        _req("https://www.facebook.com/tr/?ev=1"),
        _req("https://fls.doubleclick.net/activityi?flo=1"),
        _req("https://www.notfacebook.com/tr/?ev=1"),  # must NOT match
        _req("https://unrelated.example.com/x"),
    ]
    filtered = capture.filter_requests(requests)
    assert [r.url for r in filtered] == [
        "https://www.facebook.com/tr/?ev=1",
        "https://fls.doubleclick.net/activityi?flo=1",
    ]


def test_filter_requests_no_filters_returns_all():
    capture = NetworkCapture()
    requests = [_req("https://a.com/1"), _req("https://b.com/2")]
    assert capture.filter_requests(requests) == requests