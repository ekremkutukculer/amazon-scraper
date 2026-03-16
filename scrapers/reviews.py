"""Amazon product reviews — parse individual reviews and paginate."""

import re
import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from scrapers.base import BrowserManager

logger = logging.getLogger(__name__)


def parse_review(review_el) -> dict:
    """Extract fields from a single Amazon review element."""
    review = {
        "author": None,
        "rating": None,
        "title": None,
        "text": None,
        "date": None,
        "verified": False,
        "helpful_count": 0,
        "variant": None,
    }

    # Author
    try:
        author_el = review_el.select_one(".a-profile-name")
        if author_el:
            review["author"] = author_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Author parse error: %s", e)

    # Rating
    try:
        star_el = review_el.select_one(
            'i[data-hook="review-star-rating"], '
            'i[data-hook="cmps-review-star-rating"]'
        )
        if star_el:
            icon_alt = star_el.select_one("span.a-icon-alt")
            if icon_alt:
                match = re.search(r"([\d.]+)\s+out of", icon_alt.get_text())
                if match:
                    review["rating"] = float(match.group(1))
    except Exception as e:
        logger.warning("Rating parse error: %s", e)

    # Title — last span that doesn't contain "out of"
    try:
        title_el = review_el.select_one('a[data-hook="review-title"]')
        if title_el:
            spans = title_el.find_all("span")
            for span in reversed(spans):
                text = span.get_text(strip=True)
                if text and "out of" not in text:
                    review["title"] = text
                    break
            # Fallback: use full text if no suitable span found
            if not review["title"]:
                review["title"] = title_el.get_text(strip=True)
        else:
            # Some reviews use span instead of a for title
            title_span = review_el.select_one('span[data-hook="review-title"]')
            if title_span:
                spans = title_span.find_all("span")
                for span in reversed(spans):
                    text = span.get_text(strip=True)
                    if text and "out of" not in text:
                        review["title"] = text
                        break
                if not review["title"]:
                    review["title"] = title_span.get_text(strip=True)
    except Exception as e:
        logger.warning("Title parse error: %s", e)

    # Text
    try:
        text_el = review_el.select_one('span[data-hook="review-body"]')
        if text_el:
            review["text"] = text_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Text parse error: %s", e)

    # Date
    try:
        date_el = review_el.select_one('span[data-hook="review-date"]')
        if date_el:
            date_text = date_el.get_text(strip=True)
            match = re.search(r"on\s+(.+)$", date_text)
            if match:
                parsed_date = dateutil_parser.parse(match.group(1))
                review["date"] = parsed_date.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning("Date parse error: %s", e)

    # Verified purchase
    try:
        verified_el = review_el.select_one('span[data-hook="avp-badge"]')
        review["verified"] = verified_el is not None
    except Exception:
        pass

    # Helpful count
    try:
        helpful_el = review_el.select_one(
            'span[data-hook="helpful-vote-statement"]'
        )
        if helpful_el:
            helpful_text = helpful_el.get_text(strip=True)
            match = re.search(r"(\d+)\s+people?", helpful_text)
            if match:
                review["helpful_count"] = int(match.group(1))
            elif "One person" in helpful_text or "one person" in helpful_text:
                review["helpful_count"] = 1
    except Exception as e:
        logger.warning("Helpful count parse error: %s", e)

    # Variant (e.g., "Color: Black")
    try:
        variant_el = review_el.select_one('a[data-hook="format-strip"]')
        if variant_el:
            review["variant"] = variant_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Variant parse error: %s", e)

    return review


def scrape_reviews(asin: str, max_pages: int = 10) -> list[dict]:
    """Scrape reviews using BrowserManager.

    Each review gets asin + scraped_at fields added.
    """
    all_reviews = []

    with BrowserManager() as bm:
        for page_num in range(1, max_pages + 1):
            url = (
                f"https://www.amazon.com/product-reviews/{asin}/"
                f"?pageNumber={page_num}"
            )

            html = bm.get_page(url)
            if html is None:
                break

            # 503/error sayfasi kontrolu (gercek sayfa >10KB)
            if len(html) < 10000:
                logger.warning("Page %d: short response (%d bytes), likely blocked.", page_num, len(html))
                break

            soup = BeautifulSoup(html, "lxml")
            review_els = soup.find_all("div", {"data-hook": "review"})

            if not review_els:
                logger.info("No reviews on page %d, stopping.", page_num)
                break

            for el in review_els:
                review = parse_review(el)
                review["asin"] = asin
                review["scraped_at"] = datetime.now(timezone.utc).isoformat()
                all_reviews.append(review)

            logger.info(
                "Page %d: %d reviews found", page_num, len(review_els)
            )

            if page_num < max_pages:
                bm.delay()

    return all_reviews
