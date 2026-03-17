from bs4 import BeautifulSoup

from scrapers.search import parse_product_card

SAMPLE_HTML = """
<div data-component-type="s-search-result" data-asin="B09V3KXJPB">
  <h2 class="a-size-mini"><a class="a-link-normal"><span>Wireless Bluetooth Headphones</span></a></h2>
  <span class="a-price"><span class="a-offscreen">$29.99</span></span>
  <span class="a-icon-alt">4.5 out of 5 stars</span>
  <a href="/dp/B09V3KXJPB#customerReviews" aria-label="12,345 ratings"><span>(12K)</span></a>
  <span class="a-color-state">In Stock</span>
</div>
"""

# Real Amazon HTML structure (TRY price, aria-label reviews)
REAL_HTML = """
<div data-component-type="s-search-result" data-asin="B0BVM1PSYN">
  <h2 class="a-size-medium"><a class="a-link-normal"><span>Amazon Basics Bluetooth Headphones</span></a></h2>
  <span class="a-icon-alt">4.1 out of 5 stars</span>
  <a href="/dp/B0BVM1PSYN#customerReviews" aria-label="2,105 ratings"><span>(2.1K)</span></a>
  <span class="a-color-base">TRY 663.68</span>
</div>
"""


def _parse(html):
    soup = BeautifulSoup(html, "lxml")
    card = soup.find("div", {"data-component-type": "s-search-result"})
    return parse_product_card(card)


def test_parse_product_card_extracts_name():
    product = _parse(SAMPLE_HTML)
    assert product["name"] == "Wireless Bluetooth Headphones"


def test_parse_product_card_extracts_price_offscreen():
    product = _parse(SAMPLE_HTML)
    assert product["price"] == 29.99


def test_parse_product_card_extracts_rating():
    product = _parse(SAMPLE_HTML)
    assert product["rating"] == 4.5


def test_parse_product_card_extracts_reviews_from_aria():
    product = _parse(SAMPLE_HTML)
    assert product["reviews"] == 12345


def test_parse_product_card_handles_missing_price():
    html = """
    <div data-component-type="s-search-result" data-asin="B09V3KXJPB">
      <h2 class="a-size-mini"><a class="a-link-normal"><span>Some Product</span></a></h2>
      <span class="a-icon-alt">3.0 out of 5 stars</span>
    </div>
    """
    product = _parse(html)
    assert product["price"] is None
    assert product["name"] == "Some Product"


def test_parse_real_html_extracts_try_price():
    product = _parse(REAL_HTML)
    assert product["price"] == 663.68


def test_parse_real_html_extracts_reviews():
    product = _parse(REAL_HTML)
    assert product["reviews"] == 2105


def test_parse_real_html_extracts_rating():
    product = _parse(REAL_HTML)
    assert product["rating"] == 4.1


def test_parse_product_card_has_scraped_at():
    product = _parse(SAMPLE_HTML)
    assert "scraped_at" in product
    assert product["scraped_at"] is not None
