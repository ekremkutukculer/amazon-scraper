"""Tests for scrapers.product_detail using a saved HTML fixture."""

import pathlib

from bs4 import BeautifulSoup

from scrapers.product_detail import parse_product_detail

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "product_detail.html"
ASIN = "B09XS7JWHH"

EXPECTED_FIELDS = [
    "asin", "title", "price", "description", "bullet_points",
    "images", "variants", "seller", "availability", "category",
    "best_seller_rank", "rating", "reviews_count", "scraped_at",
]


def _parse_fixture() -> dict:
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    return parse_product_detail(soup, ASIN)


def test_parse_title():
    product = _parse_fixture()
    assert product["title"] is not None
    assert len(product["title"]) > 5


def test_parse_bullet_points():
    product = _parse_fixture()
    assert isinstance(product["bullet_points"], list)
    assert len(product["bullet_points"]) > 0


def test_parse_returns_all_fields():
    product = _parse_fixture()
    for field in EXPECTED_FIELDS:
        assert field in product, f"Missing field: {field}"


def test_parse_price():
    product = _parse_fixture()
    assert product["price"] is None or isinstance(product["price"], float)


def test_parse_price_value():
    product = _parse_fixture()
    assert product["price"] == 278.00


def test_parse_rating():
    product = _parse_fixture()
    assert product["rating"] == 4.6


def test_parse_reviews_count():
    product = _parse_fixture()
    assert product["reviews_count"] == 28547


def test_parse_availability():
    product = _parse_fixture()
    assert product["availability"] == "In Stock"


def test_parse_category():
    product = _parse_fixture()
    assert product["category"] == "Electronics > Headphones > Over-Ear Headphones"


def test_parse_variants():
    product = _parse_fixture()
    assert len(product["variants"]) == 3
    names = [v["name"] for v in product["variants"]]
    assert "Black" in names
    assert "Silver" in names
    # Silver is unavailable
    silver = [v for v in product["variants"] if v["name"] == "Silver"][0]
    assert silver["available"] is False


def test_parse_images_skips_sprites():
    product = _parse_fixture()
    for url in product["images"]:
        assert not url.endswith(".gif")


def test_parse_description():
    product = _parse_fixture()
    assert product["description"] is not None
    assert "noise cancellation" in product["description"].lower()


def test_parse_seller():
    product = _parse_fixture()
    assert product["seller"] == "TechDeals Official"


def test_parse_best_seller_rank():
    product = _parse_fixture()
    assert product["best_seller_rank"] is not None
    assert "#15" in product["best_seller_rank"]


def test_parse_scraped_at():
    product = _parse_fixture()
    assert product["scraped_at"] is not None
