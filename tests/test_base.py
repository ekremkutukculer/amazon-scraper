"""Tests for scrapers.base.BrowserManager with mocked Playwright."""

from unittest.mock import MagicMock, patch


def _build_playwright_mock(page_content="<html><body>OK</body></html>"):
    """Return a mock playwright stack: (pw, browser, context, page)."""
    page = MagicMock()
    page.content.return_value = page_content
    page.goto.return_value = None
    page.wait_for_timeout.return_value = None
    page.wait_for_selector.return_value = None
    page.add_init_script.return_value = None

    context = MagicMock()
    context.new_page.return_value = page
    context.add_cookies.return_value = None

    browser = MagicMock()
    browser.new_context.return_value = context
    browser.close.return_value = None

    pw = MagicMock()
    pw.chromium.launch.return_value = browser
    pw.stop.return_value = None

    return pw, browser, context, page


@patch("scrapers.base.sync_playwright")
def test_browser_manager_context_manager(mock_sync_pw):
    """Browser launches on enter and closes on exit."""
    pw, browser, _ctx, _page = _build_playwright_mock()
    mock_sync_pw.return_value.start.return_value = pw

    from scrapers.base import BrowserManager

    with BrowserManager() as bm:
        # Browser should have been launched
        pw.chromium.launch.assert_called_once()
        assert bm is not None

    # After exiting, browser.close should have been called
    browser.close.assert_called_once()
    pw.stop.assert_called_once()


@patch("scrapers.base.sync_playwright")
def test_browser_manager_get_page_returns_none_on_captcha(mock_sync_pw):
    """get_page returns None when CAPTCHA (validateCaptcha) is in the HTML."""
    captcha_html = '<html><form action="/errors/validateCaptcha">Enter CAPTCHA</form></html>'
    pw, _browser, _ctx, _page = _build_playwright_mock(page_content=captcha_html)
    mock_sync_pw.return_value.start.return_value = pw

    from scrapers.base import BrowserManager

    with BrowserManager() as bm:
        result = bm.get_page("https://www.amazon.com/s?k=test")

    assert result is None
