# Amazon Scraper Expansion — Design Spec

**Date:** 2026-03-17
**Status:** Approved
**Goal:** Expand Amazon scraper from search-only to full product intelligence (detail pages + review scraping) for Fiverr freelance service.

## Context

Current scraper extracts 10 fields from Amazon search results pages. This expansion adds product detail page scraping and review extraction, enabling high-value Fiverr gigs: competitor analysis, product research, and review data extraction.

## Target Users

- E-commerce sellers (competitor/market analysis)
- Dropshippers (product discovery)
- Brand/marketing agencies (review insights)

**Delivery model:** Data files (CSV/Excel/JSON). Dashboard serves as portfolio demo only.

## Architecture

### Modular Pipeline

```
scrapers/
  base.py              — Shared browser management, stealth, retry, CAPTCHA
  search.py            — Search results scraping (refactored from ecommerce_scraper.py)
  product_detail.py    — Single product detail page scraping
  reviews.py           — Product review scraping
utils/
  export.py            — CSV/Excel/JSON + multi-sheet Excel export
dashboard/
  app.py               — Extended with Product Detail and Reviews tabs
config.py              — Extended configuration
tests/
  test_search.py       — Renamed from test_scraper.py
  test_product_detail.py
  test_reviews.py
  test_base.py
  test_export.py       — Existing
```

### base.py — Shared Infrastructure

Provides `BrowserManager` context manager used by all scraper modules.

Responsibilities:
- Launch headless Chromium with stealth args (disable AutomationControlled, no-sandbox)
- Set navigator.webdriver override via init_script
- Random User-Agent rotation from config
- Realistic browser headers (Sec-Fetch-*, DNT, Accept)
- USD cookie (i18n-prefs=USD)
- Page navigation with retry (3 attempts, random backoff 3-6s)
- CAPTCHA detection (validateCaptcha form)
- Random delays between requests (DELAY_RANGE from config)

Batch functions use a single BrowserManager context for all requests, reusing the browser instance to minimize launches and detection risk.

Usage pattern:
```python
with BrowserManager() as bm:
    html = bm.get_page("https://www.amazon.com/dp/B0XXXXX")
    # parse html with BeautifulSoup

# Batch: one browser, multiple pages
with BrowserManager() as bm:
    for asin in asins:
        html = bm.get_page(f"https://www.amazon.com/dp/{asin}")
        # parse each
```

### search.py — Search Results

Refactored from `ecommerce_scraper.py`. Same functionality, uses `BrowserManager` instead of inline Playwright setup. Function renamed from `scrape_amazon` to `search_products` — dashboard import must be updated accordingly.

Functions:
- `search_products(search_term, max_pages) -> list[dict]`
- `parse_product_card(card) -> dict`

Fields (11):
- name, price, rating, reviews, stock, asin, brand, image_url, product_url, badge, scraped_at

All modules add `scraped_at` (ISO timestamp) to each record for client reference.

### product_detail.py — Product Detail Page

Scrapes `https://www.amazon.com/dp/{asin}`.

Function:
- `scrape_product_detail(asin) -> dict`
- `scrape_product_details(asins: list[str]) -> list[dict]` (batch, sequential with delays)

Fields (12):

| Field | Selector/Source | Type |
|-------|----------------|------|
| asin | input param | str |
| title | `#productTitle` | str |
| price | existing 3-method fallback | float |
| description | `#productDescription` | str |
| bullet_points | `#feature-bullets li` | list[str] |
| images | `#imgTagWrapperId img` (main) + `#altImages img` (gallery) | list[str] |
| variants | `.swatchAvailable` + `.swatchUnavailable` (best-effort, may vary by category) | list[dict] `{"name": str, "asin": str, "available": bool}` |
| seller | `#sellerProfileTriggerId` or `#merchant-info` | str |
| availability | `#availability span` | str |
| category | `#wayfinding-breadcrumbs_feature_div` | str |
| best_seller_rank | `#productDetails_detailBullets_sections1` BSR row, fallback `#SalesRank` | str |
| rating | existing method | float |
| reviews_count | existing method | int |

### reviews.py — Review Scraping

Scrapes `https://www.amazon.com/product-reviews/{asin}/?pageNumber={n}`.

Functions:
- `scrape_reviews(asin, max_pages=10) -> list[dict]`
- `parse_review(review_el) -> dict`

Fields (8):

| Field | Selector/Source | Type |
|-------|----------------|------|
| author | `.a-profile-name` | str |
| rating | `.review-rating .a-icon-alt` | float |
| title | `.review-title span` | str |
| text | `.review-text-content span` | str |
| date | `.review-date`, parsed to ISO format (YYYY-MM-DD) | str |
| verified | `.avp-badge` presence | bool |
| helpful_count | `.cr-vote-text`, regex `r"(\d+) people?"` with fallback 1 for "One person" | int |
| variant | `.review-format-strip` | str |

Pagination: follow "Next page" link or stop when no more reviews.

### export.py — Extended Export

Existing functions unchanged. New addition:
- `export_multi_sheet_excel(search_data, detail_data, review_data, filepath)` — Writes 3 sheets to a single .xlsx file

## Usage Flow (Fiverr Gig)

```
Client: "Analyze top wireless headphones on Amazon"

Step 1: search_products("wireless headphones", max_pages=3)
        → ~48 products

Step 2: scrape_product_details(top_10_asins)
        → 10 detailed product profiles

Step 3: scrape_reviews(asin, max_pages=5) × 10 products
        → ~500 reviews total

Step 4: Export to multi-sheet Excel:
        Sheet 1 — Product comparison table
        Sheet 2 — Detailed product info
        Sheet 3 — All reviews
```

## Dashboard Extension

Add tabs to existing Streamlit dashboard:

- **Search** tab (existing) — search + filter + charts
- **Product Detail** tab — ASIN input → detail card display
- **Reviews** tab — ASIN input → review table + rating distribution chart

## Test Strategy

All parser functions tested with saved HTML fixtures (no live Amazon calls in tests).

- `test_base.py` — BrowserManager context manager, retry logic, CAPTCHA detection (mocked)
- `test_search.py` — Renamed from test_scraper.py, existing 8 tests
- `test_product_detail.py` — Parse detail page HTML fixtures (title, bullets, BSR, variants)
- `test_reviews.py` — Parse review HTML fixtures (rating, text, verified, helpful_count)
- `test_export.py` — Existing 3 tests

Target: 20+ tests total.

## Out of Scope

- Sentiment analysis / NLP on reviews
- Price tracking over time (requires scheduling + database)
- Multi-site scraping (eBay, Trendyol etc.)
- CAPTCHA solving
- Proxy rotation
- Hosting / deployment of dashboard
- Async / concurrent scraping

## Risks

| Risk | Mitigation |
|------|-----------|
| Amazon blocks detail page scraping | Stealth mode + random delays + retry |
| Review page structure changes | Multiple selector fallbacks like price parsing |
| Rate limiting on batch scraping | Conservative delays (2-5s), max 10 products per batch |
| CAPTCHA on review pages | Detection + graceful stop, user notified |
