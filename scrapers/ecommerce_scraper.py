import re
import time
import random
import logging

import httpx
from bs4 import BeautifulSoup

from config import DELAY_RANGE, MAX_PAGES, PROXY, get_random_user_agent

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def parse_product_card(card) -> dict:
    """Tek bir Amazon arama sonucu kartindan urun bilgilerini cikarir."""
    product = {
        "name": None,
        "price": None,
        "rating": None,
        "reviews": None,
        "stock": None,
        "asin": None,
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
        review_link = card.find("a", href=lambda x: x and "customerReviews" in str(x))
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

    return product


def scrape_amazon(search_term: str, max_pages: int = None) -> list[dict]:
    """Amazon'da arama yapip urun listesi dondurur."""
    if max_pages is None:
        max_pages = MAX_PAGES

    all_products = []
    client_kwargs = {"timeout": 15.0, "follow_redirects": True}
    if PROXY:
        client_kwargs["proxies"] = PROXY

    with httpx.Client(**client_kwargs) as client:
        for page in range(1, max_pages + 1):
            url = f"https://www.amazon.com/s?k={search_term}&page={page}"
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            }

            html = _fetch_with_retry(client, url, headers)
            if html is None:
                logger.warning(f"Page {page} fetch failed, stopping.")
                break

            soup = BeautifulSoup(html, "lxml")
            cards = soup.find_all("div", {"data-component-type": "s-search-result"})

            if not cards:
                logger.info(f"No results on page {page}, stopping.")
                break

            for card in cards:
                product = parse_product_card(card)
                if product["name"]:
                    all_products.append(product)

            logger.info(f"Page {page}: {len(cards)} products found")

            # Sayfa arasi bekleme
            if page < max_pages:
                delay = random.uniform(*DELAY_RANGE)
                time.sleep(delay)

    return all_products


def _fetch_with_retry(client: httpx.Client, url: str, headers: dict) -> str | None:
    """HTTP istegi gonderir, basarisiz olursa 3 kez dener."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 503:
                logger.warning(f"503 received (attempt {attempt}/{MAX_RETRIES})")
            else:
                logger.warning(f"HTTP {response.status_code} (attempt {attempt}/{MAX_RETRIES})")
        except httpx.RequestError as e:
            logger.warning(f"Request error: {e} (attempt {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            wait = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait)

    return None
