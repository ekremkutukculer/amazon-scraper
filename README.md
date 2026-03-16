# Amazon Product Scraper & Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Browser%20Automation-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready Amazon product scraper that extracts real-time pricing, ratings, and reviews using **Playwright** for full JavaScript rendering — paired with an interactive **Streamlit** dashboard for analysis and export.

## Key Features

| Feature | Description |
|---------|-------------|
| **Full JS Rendering** | Playwright-based browser automation — no broken pages from missing JS |
| **Anti-Detection** | User-Agent rotation, randomized delays, stealth headless mode |
| **USD Pricing** | Forces US locale via cookies for consistent dollar pricing |
| **Live Dashboard** | Interactive Streamlit UI with filtering, sorting, and charts |
| **Multi-Format Export** | Download results as CSV, Excel (.xlsx), or JSON |
| **Proxy Support** | Optional proxy configuration for scaling |

## Screenshots

> _Coming soon_

## Quick Start

```bash
# Clone
git clone https://github.com/ekremkutukculer/amazon-scraper.git
cd amazon-scraper

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Launch dashboard
streamlit run dashboard/app.py
```

## How It Works

```
User enters search query
        ↓
Playwright launches headless Chromium
        ↓
Navigates Amazon with US locale cookies
        ↓
BeautifulSoup parses rendered HTML
        ↓
Extracts: name, price, rating, reviews, ASIN
        ↓
Results displayed in Streamlit dashboard
        ↓
Export as CSV / Excel / JSON
```

## Project Structure

```
├── scrapers/
│   └── ecommerce_scraper.py   # Playwright scraper + parser
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── config.py                  # Settings (delays, proxy, user-agents)
├── tests/
│   └── test_scraper.py        # 11 tests (parsing, edge cases)
└── data/                      # Exported results (gitignored)
```

## Configuration

Edit `config.py` to customize:

```python
DELAY_RANGE = (2, 5)    # Seconds between requests
MAX_PAGES = 3            # Default page limit
PROXY = None             # Your proxy URL (e.g., "http://user:pass@host:port")
```

## Tech Stack

- **Scraping:** Playwright, BeautifulSoup4, lxml
- **Data:** Pandas, openpyxl
- **UI:** Streamlit
- **Testing:** pytest (11 tests, 100% pass)
- **Linting:** ruff

## Sample Output

| Product | Price | Rating | Reviews |
|---------|-------|--------|---------|
| Sony WH-1000XM5 | $278.00 | 4.6 | 12,847 |
| JBL Tune 510BT | $29.95 | 4.5 | 98,204 |
| Apple AirPods Pro | $189.99 | 4.7 | 167,532 |

*48 products scraped per run on average, with 100% rating/review coverage.*

## License

MIT — free for personal and commercial use.

## Disclaimer

This project is for **educational and portfolio purposes**. Amazon's Terms of Service restrict automated access. For production use, consider the [Amazon Product Advertising API](https://webservices.amazon.com/paapi5/documentation/).

---

Built by [@ekremkutukculer](https://github.com/ekremkutukculer)
