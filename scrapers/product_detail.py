"""Amazon product detail page — parse a single product's full information."""

import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from scrapers.base import BrowserManager

logger = logging.getLogger(__name__)


def parse_product_detail(soup: BeautifulSoup, asin: str) -> dict:
    """Extract 14 fields from an Amazon product detail page.

    Every field extraction is wrapped in try/except so a single failure
    never kills the whole parse.
    """
    product = {
        "asin": asin,
        "title": None,
        "price": None,
        "description": None,
        "bullet_points": [],
        "images": [],
        "variants": [],
        "seller": None,
        "availability": None,
        "category": None,
        "best_seller_rank": None,
        "rating": None,
        "reviews_count": None,
        "scraped_at": None,
    }

    # Title — #productTitle span
    try:
        title_el = soup.find("span", id="productTitle")
        if title_el:
            product["title"] = title_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Title parse error: %s", e)

    # Price — 3-method fallback
    try:
        price_found = False

        # Method 1: a-offscreen
        price_el = soup.find("span", class_="a-offscreen")
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_clean = re.sub(r"[^\d.]", "", price_text)
            if price_clean:
                product["price"] = float(price_clean)
                price_found = True

        # Method 2: a-price-whole + a-price-fraction
        if not price_found:
            whole = soup.find("span", class_="a-price-whole")
            frac = soup.find("span", class_="a-price-fraction")
            if whole:
                whole_text = whole.get_text(strip=True).rstrip(".")
                frac_text = frac.get_text(strip=True) if frac else "00"
                price_clean = re.sub(r"[^\d]", "", whole_text)
                if price_clean:
                    product["price"] = float(f"{price_clean}.{frac_text}")
                    price_found = True

        # Method 3: regex fallback on page text
        if not price_found:
            price_spans = soup.find_all("span", class_="a-color-price")
            for span in price_spans:
                text = span.get_text(strip=True)
                match = re.search(r"[\$€£]([\d,]+\.?\d*)", text)
                if match:
                    val = float(match.group(1).replace(",", ""))
                    if val > 0:
                        product["price"] = val
                        break
    except (ValueError, AttributeError) as e:
        logger.warning("Price parse error: %s", e)

    # Description — #productDescription div
    try:
        desc_el = soup.find("div", id="productDescription")
        if desc_el:
            product["description"] = desc_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Description parse error: %s", e)

    # Bullet points — #feature-bullets li
    try:
        bullets_div = soup.find("div", id="feature-bullets")
        if bullets_div:
            items = bullets_div.find_all("li")
            product["bullet_points"] = [
                li.get_text(strip=True) for li in items if li.get_text(strip=True)
            ]
    except Exception as e:
        logger.warning("Bullet points parse error: %s", e)

    # Images — main image + gallery (skip sprites/gifs)
    try:
        images = []
        # Main image
        main_wrapper = soup.find("div", id="imgTagWrapperId")
        if main_wrapper:
            main_img = main_wrapper.find("img")
            if main_img:
                src = main_img.get("data-old-hires") or main_img.get("src")
                if src:
                    images.append(src)

        # Gallery images (skip sprite images ending in .gif)
        alt_images = soup.find("div", id="altImages")
        if alt_images:
            for img in alt_images.find_all("img"):
                src = img.get("src", "")
                if src and not src.endswith(".gif"):
                    images.append(src)

        product["images"] = images
    except Exception as e:
        logger.warning("Images parse error: %s", e)

    # Variants — .swatchAvailable + .swatchUnavailable
    try:
        variants = []
        for swatch in soup.find_all("li", class_=re.compile(r"swatch(Available|Unavailable)")):
            variant = {
                "name": None,
                "asin": swatch.get("data-defaultasin"),
                "available": "swatchAvailable" in swatch.get("class", []),
            }
            text_el = swatch.find("span", class_="a-button-text")
            if text_el:
                variant["name"] = text_el.get_text(strip=True)
            variants.append(variant)
        product["variants"] = variants
    except Exception as e:
        logger.warning("Variants parse error: %s", e)

    # Seller — #sellerProfileTriggerId or #merchant-info
    try:
        seller_el = soup.find("a", id="sellerProfileTriggerId")
        if seller_el:
            product["seller"] = seller_el.get_text(strip=True)
        else:
            merchant_el = soup.find("div", id="merchant-info")
            if merchant_el:
                product["seller"] = merchant_el.get_text(strip=True)
    except Exception as e:
        logger.warning("Seller parse error: %s", e)

    # Availability — #availability span
    try:
        avail_div = soup.find("div", id="availability")
        if avail_div:
            span = avail_div.find("span")
            if span:
                product["availability"] = span.get_text(strip=True)
    except Exception as e:
        logger.warning("Availability parse error: %s", e)

    # Category — breadcrumbs joined with " > "
    try:
        breadcrumbs_div = soup.find("div", id="wayfinding-breadcrumbs_feature_div")
        if breadcrumbs_div:
            links = breadcrumbs_div.find_all("a")
            if links:
                product["category"] = " > ".join(
                    a.get_text(strip=True) for a in links
                )
    except Exception as e:
        logger.warning("Category parse error: %s", e)

    # Best Seller Rank — #productDetails_detailBullets_sections1, fallback #SalesRank
    try:
        bsr = None
        details_table = soup.find("table", id="productDetails_detailBullets_sections1")
        if details_table:
            for row in details_table.find_all("tr"):
                th = row.find("th")
                if th and "Best Sellers Rank" in th.get_text():
                    td = row.find("td")
                    if td:
                        bsr = td.get_text(strip=True)
                    break
        if not bsr:
            sales_rank = soup.find("li", id="SalesRank")
            if not sales_rank:
                sales_rank = soup.find("tr", id="SalesRank")
            if sales_rank:
                bsr = sales_rank.get_text(strip=True)
        product["best_seller_rank"] = bsr
    except Exception as e:
        logger.warning("BSR parse error: %s", e)

    # Rating — span.a-icon-alt with "X out of" regex
    try:
        for span in soup.find_all("span", class_="a-icon-alt"):
            text = span.get_text(strip=True)
            match = re.search(r"([\d.]+)\s+out of", text)
            if match:
                product["rating"] = float(match.group(1))
                break
    except (ValueError, AttributeError) as e:
        logger.warning("Rating parse error: %s", e)

    # Reviews count — #acrCustomerReviewCount span
    try:
        reviews_el = soup.find("span", id="acrCustomerReviewCount")
        if reviews_el:
            text = reviews_el.get_text(strip=True)
            match = re.search(r"([\d,]+)", text)
            if match:
                product["reviews_count"] = int(match.group(1).replace(",", ""))
    except (ValueError, AttributeError) as e:
        logger.warning("Reviews count parse error: %s", e)

    product["scraped_at"] = datetime.now(timezone.utc).isoformat()

    return product


def scrape_product_detail(asin: str) -> dict:
    """Scrape a single Amazon product detail page using BrowserManager."""
    url = f"https://www.amazon.com/dp/{asin}"
    with BrowserManager() as bm:
        html = bm.get_page(url, wait_selector="#productTitle")
        if html is None:
            logger.warning("Failed to fetch product page for ASIN %s", asin)
            return {"asin": asin, "error": "fetch_failed"}

        soup = BeautifulSoup(html, "lxml")
        return parse_product_detail(soup, asin)


def scrape_product_details(asins: list[str]) -> list[dict]:
    """Scrape multiple Amazon products in one browser session with delays."""
    results = []
    with BrowserManager() as bm:
        for i, asin in enumerate(asins):
            url = f"https://www.amazon.com/dp/{asin}"
            html = bm.get_page(url, wait_selector="#productTitle")

            if html is None:
                logger.warning("Failed to fetch ASIN %s", asin)
                results.append({"asin": asin, "error": "fetch_failed"})
            else:
                soup = BeautifulSoup(html, "lxml")
                results.append(parse_product_detail(soup, asin))

            # Delay between requests (skip after last)
            if i < len(asins) - 1:
                bm.delay()

    return results
