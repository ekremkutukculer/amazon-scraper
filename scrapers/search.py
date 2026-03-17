"""Amazon product search — parse cards and paginate through results."""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup, Tag

from config import MAX_PAGES
from scrapers.base import BrowserManager

logger = logging.getLogger(__name__)


def parse_product_card(card: Tag) -> dict[str, Any] | None:
    """Tek bir Amazon arama sonucu kartindan urun bilgilerini cikarir."""
    product = {
        "name": None,
        "price": None,
        "rating": None,
        "reviews": None,
        "stock": None,
        "asin": None,
        "brand": None,
        "image_url": None,
        "product_url": None,
        "badge": None,
    }

    try:
        product["asin"] = card.get("data-asin")
    except Exception:
        pass

    # Urun adi
    try:
        h2 = card.find("h2")
        if h2:
            product["name"] = h2.get_text(strip=True)
    except Exception as e:
        logger.warning(f"Name parse error: {e}")

    # Fiyat — birden fazla selector dener
    try:
        price_found = False
        # Yontem 1: a-offscreen (standart Amazon fiyat)
        price_el = card.find("span", class_="a-offscreen")
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_clean = re.sub(r"[^\d.]", "", price_text)
            if price_clean:
                product["price"] = float(price_clean)
                price_found = True

        # Yontem 2: a-price-whole + a-price-fraction
        if not price_found:
            whole = card.find("span", class_="a-price-whole")
            frac = card.find("span", class_="a-price-fraction")
            if whole:
                whole_text = whole.get_text(strip=True).rstrip(".")
                frac_text = frac.get_text(strip=True) if frac else "00"
                price_clean = re.sub(r"[^\d]", "", whole_text)
                if price_clean:
                    product["price"] = float(f"{price_clean}.{frac_text}")
                    price_found = True

        # Yontem 3: secondary offer (TRY/USD/EUR text in a-color-base)
        if not price_found:
            for span in card.find_all("span", class_="a-color-base"):
                text = span.get_text(strip=True)
                # Normalize whitespace (non-breaking spaces etc.)
                text = re.sub(r"\s+", " ", text.replace("\xa0", " "))
                # Match currency patterns: $29.99, TRY 5,080.11, €19.99
                price_match = re.search(
                    r"(?:[\$€£]|TRY|USD|EUR|GBP)\s*([\d,]+\.?\d*)", text
                )
                if price_match:
                    price_str = price_match.group(1).replace(",", "")
                    try:
                        val = float(price_str)
                        if val > 0:
                            product["price"] = val
                            price_found = True
                            break
                    except ValueError:
                        continue
    except (ValueError, AttributeError) as e:
        logger.warning(f"Price parse error: {e}")

    # Rating
    try:
        rating_el = card.find("span", class_="a-icon-alt")
        if rating_el:
            rating_text = rating_el.get_text(strip=True)
            match = re.search(r"([\d.]+)\s+out of", rating_text)
            if match:
                product["rating"] = float(match.group(1))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Rating parse error: {e}")

    # Yorum sayisi — aria-label'dan veya text'ten
    try:
        reviews_found = False
        # Yontem 1: aria-label="X ratings" (customerReviews link)
        review_link = card.find(
            "a", href=lambda x: x and "customerReviews" in str(x)
        )
        if review_link:
            aria = review_link.get("aria-label", "")
            match = re.search(r"([\d,]+)\s+rating", aria)
            if match:
                product["reviews"] = int(match.group(1).replace(",", ""))
                reviews_found = True

        # Yontem 2: eski yontem — span.a-size-base
        if not reviews_found:
            reviews_el = card.find(
                "span", class_="a-size-base", string=re.compile(r"^[\d,]+$")
            )
            if reviews_el:
                reviews_text = reviews_el.get_text(strip=True).replace(",", "")
                if reviews_text.isdigit():
                    product["reviews"] = int(reviews_text)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Reviews parse error: {e}")

    # Stok durumu
    try:
        stock_el = card.find("span", class_="a-color-state")
        if stock_el:
            product["stock"] = stock_el.get_text(strip=True)
    except Exception:
        pass

    # Urun resmi
    try:
        img_el = card.find("img", class_="s-image")
        if img_el:
            product["image_url"] = img_el.get("src")
    except Exception:
        pass

    # Urun linki
    try:
        link_el = card.find("a", class_="a-link-normal", href=re.compile(r"/dp/"))
        if not link_el:
            h2 = card.find("h2")
            if h2:
                link_el = h2.find("a")
        if link_el:
            href = link_el.get("href", "")
            if href.startswith("/"):
                href = "https://www.amazon.com" + href
            product["product_url"] = href
    except Exception:
        pass

    # Marka
    try:
        # Yontem 1: "by Brand" text
        by_el = card.find("span", class_="a-size-base-plus")
        if by_el:
            product["brand"] = by_el.get_text(strip=True)
        # Yontem 2: isimden cikart (ilk kelime genelde marka)
        if not product["brand"] and product["name"]:
            product["brand"] = product["name"].split()[0]
    except Exception:
        pass

    # Badge (Best Seller, Amazon's Choice, vb.)
    try:
        badge_el = card.find("span", class_="a-badge-text")
        if badge_el:
            product["badge"] = badge_el.get_text(strip=True)
    except Exception:
        pass

    product["scraped_at"] = datetime.now(timezone.utc).isoformat()

    return product


def search_products(search_term: str, max_pages: int | None = None) -> list[dict[str, Any]]:
    """Search Amazon and return a list of product dicts."""
    if max_pages is None:
        max_pages = MAX_PAGES

    all_products = []
    seen_asins = set()

    with BrowserManager() as bm:
        for page_num in range(1, max_pages + 1):
            url = f"https://www.amazon.com/s?k={search_term}&page={page_num}"

            html = bm.get_page(
                url,
                wait_selector='[data-component-type="s-search-result"]',
            )
            if html is None:
                break

            soup = BeautifulSoup(html, "lxml")
            cards = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )

            if not cards:
                logger.info(f"No results on page {page_num}, stopping.")
                break

            for card in cards:
                product = parse_product_card(card)
                if product["name"] and len(product["name"]) > 5:
                    asin = product.get("asin")
                    if asin:
                        if asin in seen_asins:
                            continue
                        seen_asins.add(asin)
                    all_products.append(product)

            logger.info(f"Page {page_num}: {len(cards)} products found")

            if page_num < max_pages:
                bm.delay()

    return all_products
