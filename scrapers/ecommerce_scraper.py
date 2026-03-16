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

    # Fiyat
    try:
        price_el = card.find("span", class_="a-offscreen")
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_clean = re.sub(r"[^\d.]", "", price_text)
            product["price"] = float(price_clean) if price_clean else None
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

    # Yorum sayisi
    try:
        reviews_el = card.find("span", class_="a-size-base", string=re.compile(r"[\d,]+"))
        if reviews_el:
            reviews_text = reviews_el.get_text(strip=True).replace(",", "")
            product["reviews"] = int(reviews_text) if reviews_text.isdigit() else None
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
