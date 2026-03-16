import re
import random
import logging

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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

    return product


def scrape_amazon(search_term: str, max_pages: int = None) -> list[dict]:
    """Playwright ile Amazon'da arama yapip urun listesi dondurur."""
    if max_pages is None:
        max_pages = MAX_PAGES

    all_products = []
    seen_asins = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        context_kwargs = {
            "user_agent": get_random_user_agent(),
            "locale": "en-US",
            "viewport": {"width": 1920, "height": 1080},
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        }
        if PROXY:
            context_kwargs["proxy"] = {"server": PROXY}

        context = browser.new_context(**context_kwargs)

        # USD para birimi icin cookie ayarla
        context.add_cookies([{
            "name": "i18n-prefs",
            "value": "USD",
            "domain": ".amazon.com",
            "path": "/",
        }])

        page = context.new_page()

        # navigator.webdriver gizle (bot tespitini atlatir)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
        """)

        for page_num in range(1, max_pages + 1):
            url = f"https://www.amazon.com/s?k={search_term}&page={page_num}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(random.randint(2000, 4000))

                # Sayfanin yuklendiginden emin ol
                page.wait_for_selector(
                    '[data-component-type="s-search-result"]', timeout=10000
                )
            except Exception as e:
                logger.warning(f"Page {page_num} load failed: {e}")
                break

            html = page.content()
            soup = BeautifulSoup(html, "lxml")

            # CAPTCHA tespiti
            if soup.find("form", action=re.compile(r"validateCaptcha")):
                logger.warning(f"Page {page_num}: CAPTCHA detected, stopping.")
                break

            cards = soup.find_all(
                "div", {"data-component-type": "s-search-result"}
            )

            if not cards:
                logger.info(f"No results on page {page_num}, stopping.")
                break

            for card in cards:
                product = parse_product_card(card)
                if product["name"] and len(product["name"]) > 5:
                    # Duplicate filtresi (ASIN bazli)
                    asin = product.get("asin")
                    if asin:
                        if asin in seen_asins:
                            continue
                        seen_asins.add(asin)
                    all_products.append(product)

            logger.info(f"Page {page_num}: {len(cards)} products found")

            # Sayfa arasi bekleme
            if page_num < max_pages:
                delay = random.uniform(*DELAY_RANGE)
                page.wait_for_timeout(int(delay * 1000))

        browser.close()

    return all_products
