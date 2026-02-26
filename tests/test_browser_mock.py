import pytest
from unittest.mock import AsyncMock, MagicMock
from src.browser.browser import BrowserManager
from src.models import NetworkRequest

@pytest.fixture
def mock_playwright(mocker):
    """Mocks the entire Playwright async API structure."""
    # Mock the individual components
    mock_page = AsyncMock()
    mock_browser = AsyncMock()
    mock_chromium = AsyncMock()

    # This mock represents the object returned by `async_playwright()`
    mock_playwright_context = AsyncMock()

    # Configure the chained calls from mock_playwright_context
    mock_playwright_context.chromium = mock_chromium
    mock_chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page

    # Patch the `async_playwright` function directly to return our configured mock_playwright_context
    mocker.patch("src.browser.browser.async_playwright", return_value=mock_playwright_context)
    
    # We also need to mock the `start` method of the `mock_playwright_context`
    # because `BrowserManager.launch` awaits `async_playwright().start()`
    mock_playwright_context.start.return_value = mock_playwright_context # It returns itself when awaited

    # Return the specific mocks that tests will assert against
    return mock_playwright_context, mock_browser, mock_page
@pytest.mark.asyncio
async def test_browser_manager_launch(mock_playwright):
    _, mock_browser, mock_page = mock_playwright
    manager = BrowserManager(headless=True)
    
    page = await manager.launch()
    
    mock_browser.new_page.assert_called_once()
    assert page == mock_page
    assert manager.page == mock_page
    mock_page.on.assert_called_once_with("request", manager._handle_request)

@pytest.mark.asyncio
async def test_browser_manager_navigate(mock_playwright):
    _, _, mock_page = mock_playwright
    manager = BrowserManager(headless=True)
    await manager.launch() # Launch first to set up page object

    test_url = "http://example.com"
    await manager.navigate(test_url)

    mock_page.goto.assert_called_once_with(test_url, wait_until="domcontentloaded", timeout=60000)

@pytest.mark.asyncio
async def test_browser_manager_handle_request():
    manager = BrowserManager(headless=True)
    # Simulate a request object
    mock_request = MagicMock()
    mock_request.url = "http://test.com/data?param=value"
    mock_request.method = "GET"
    mock_request.headers = {"Content-Type": "application/json"}
    mock_request.post_data = "some_data"

    await manager._handle_request(mock_request)
    
    assert len(manager.captured_requests) == 1
    captured = manager.captured_requests[0]
    assert isinstance(captured, NetworkRequest)
    assert captured.url == mock_request.url
    assert captured.method == mock_request.method
    assert captured.headers == mock_request.headers
    assert captured.post_data == mock_request.post_data

@pytest.mark.asyncio
async def test_browser_manager_get_captured_requests(mock_playwright):
    _, _, mock_page = mock_playwright
    manager = BrowserManager(headless=True)
    await manager.launch()
    
    # Manually add some mock requests to simulate capture
    mock_request_1 = MagicMock(url="url1", method="GET", headers={}, post_data=None)
    mock_request_2 = MagicMock(url="url2", method="POST", headers={}, post_data="data")
    await manager._handle_request(mock_request_1)
    await manager._handle_request(mock_request_2)

    requests = manager.get_captured_requests()
    assert len(requests) == 2
    assert requests[0].url == "url1"
    assert requests[1].url == "url2"

@pytest.mark.asyncio
async def test_browser_manager_close(mock_playwright):
    mock_pw, mock_browser, mock_page = mock_playwright
    manager = BrowserManager(headless=True)
    await manager.launch()

    await manager.close()

    mock_page.remove_listener.assert_called_once_with("request", manager._handle_request)
    mock_browser.close.assert_called_once()
    mock_pw.stop.assert_called_once()
