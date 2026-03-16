"""Tests for scrapers.reviews using saved HTML fixture."""

import os

from bs4 import BeautifulSoup

from scrapers.reviews import parse_review

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "reviews.html"
)

with open(FIXTURE_PATH, "r", encoding="utf-8") as _f:
    _SOUP = BeautifulSoup(_f.read(), "lxml")

REVIEW_ELEMENTS = _SOUP.find_all("div", {"data-hook": "review"})


def _first_review():
    return parse_review(REVIEW_ELEMENTS[0])


def test_fixture_has_reviews():
    assert len(REVIEW_ELEMENTS) >= 3, "Fixture should contain at least 3 reviews"


def test_parse_review_extracts_rating():
    review = _first_review()
    assert review["rating"] is not None
    assert 1.0 <= review["rating"] <= 5.0


def test_parse_review_extracts_text():
    review = _first_review()
    assert review["text"] is not None
    assert len(review["text"]) > 10


def test_parse_review_extracts_author():
    review = _first_review()
    assert review["author"] is not None


def test_parse_review_has_all_fields():
    review = _first_review()
    expected_keys = {
        "author",
        "rating",
        "title",
        "text",
        "date",
        "verified",
        "helpful_count",
        "variant",
    }
    assert expected_keys == set(review.keys())


def test_parse_review_extracts_date_iso():
    review = _first_review()
    assert review["date"] is not None
    # Should be ISO format YYYY-MM-DD
    parts = review["date"].split("-")
    assert len(parts) == 3
    assert len(parts[0]) == 4  # year


def test_parse_review_extracts_verified():
    review = _first_review()
    assert review["verified"] is True


def test_parse_review_extracts_helpful_count():
    review = _first_review()
    assert review["helpful_count"] == 42


def test_parse_review_extracts_variant():
    review = _first_review()
    assert review["variant"] is not None
    assert "Black" in review["variant"]


def test_parse_review_extracts_title():
    review = _first_review()
    assert review["title"] is not None
    assert "out of" not in review["title"]


def test_parse_review_one_person_helpful():
    """Second review has 'One person found this helpful'."""
    review = parse_review(REVIEW_ELEMENTS[1])
    assert review["helpful_count"] == 1


def test_parse_review_no_helpful_defaults_zero():
    """Third review has no helpful votes."""
    review = parse_review(REVIEW_ELEMENTS[2])
    assert review["helpful_count"] == 0


def test_parse_review_not_verified():
    """Third review has no verified badge."""
    review = parse_review(REVIEW_ELEMENTS[2])
    assert review["verified"] is False


def test_parse_review_cmps_star_rating():
    """Fourth review uses cmps-review-star-rating instead of review-star-rating."""
    review = parse_review(REVIEW_ELEMENTS[3])
    assert review["rating"] == 5.0


def test_parse_review_span_title():
    """Fourth review uses span[data-hook=review-title] instead of a tag."""
    review = parse_review(REVIEW_ELEMENTS[3])
    assert review["title"] is not None
    assert "out of" not in review["title"]


def test_all_reviews_have_ratings():
    for el in REVIEW_ELEMENTS:
        review = parse_review(el)
        assert review["rating"] is not None
        assert 1.0 <= review["rating"] <= 5.0


def test_all_reviews_have_dates():
    for el in REVIEW_ELEMENTS:
        review = parse_review(el)
        assert review["date"] is not None
