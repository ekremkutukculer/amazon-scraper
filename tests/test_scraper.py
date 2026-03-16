from scrapers.ecommerce_scraper import parse_product_card

SAMPLE_HTML = """
<div data-component-type="s-search-result" data-asin="B09V3KXJPB">
  <h2 class="a-size-mini"><a class="a-link-normal"><span>Wireless Bluetooth Headphones</span></a></h2>
  <span class="a-price"><span class="a-offscreen">$29.99</span></span>
  <span class="a-icon-alt">4.5 out of 5 stars</span>
  <span class="a-size-base">12,345</span>
  <span class="a-color-state">In Stock</span>
</div>
"""


def test_parse_product_card_extracts_name():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(SAMPLE_HTML, "lxml")
    card = soup.find("div", {"data-component-type": "s-search-result"})
    product = parse_product_card(card)
    assert product["name"] == "Wireless Bluetooth Headphones"


def test_parse_product_card_extracts_price():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(SAMPLE_HTML, "lxml")
    card = soup.find("div", {"data-component-type": "s-search-result"})
    product = parse_product_card(card)
    assert product["price"] == 29.99


def test_parse_product_card_extracts_rating():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(SAMPLE_HTML, "lxml")
    card = soup.find("div", {"data-component-type": "s-search-result"})
    product = parse_product_card(card)
    assert product["rating"] == 4.5


def test_parse_product_card_handles_missing_price():
    from bs4 import BeautifulSoup
    html = """
    <div data-component-type="s-search-result" data-asin="B09V3KXJPB">
      <h2 class="a-size-mini"><a class="a-link-normal"><span>Some Product</span></a></h2>
      <span class="a-icon-alt">3.0 out of 5 stars</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    card = soup.find("div", {"data-component-type": "s-search-result"})
    product = parse_product_card(card)
    assert product["price"] is None
    assert product["name"] == "Some Product"
