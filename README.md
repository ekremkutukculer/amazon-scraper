# Amazon Product Intelligence Pipeline

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![CI](https://img.shields.io/github/actions/workflow/status/ekremkutukculer/amazon-scraper/ci.yml?label=tests&logo=github)](https://github.com/ekremkutukculer/amazon-scraper/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/Playwright-Stealth%20Mode-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev)

A production-ready Amazon scraper with anti-detection, 3-stage data pipeline, and interactive Streamlit dashboard.

## Features

| Feature | Description |
|---------|-------------|
| **3-Stage Pipeline** | Search results → Product details → Customer reviews |
| **Stealth Mode** | Webdriver masking, user-agent rotation, randomized delays |
| **Anti-Detection** | CAPTCHA detection, 503 handling, exponential retry |
| **Interactive Dashboard** | Real-time filtering, charts, and brand analysis |
| **Multi-Format Export** | CSV, Excel (.xlsx with multiple sheets), JSON |
| **Proxy Support** | Optional proxy configuration for scaling |

## Architecture

```mermaid
flowchart LR
    A[Search Query] --> B[Playwright + Stealth]
    B --> C[Search Results]
    C --> D[Product Details]
    D --> E[Customer Reviews]
    E --> F{Export}
    F --> G[CSV]
    F --> H[Excel]
    F --> I[JSON]
    F --> J[Dashboard]
```

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

## Docker

```bash
docker-compose up
# Dashboard available at http://localhost:8501
```

## Dashboard

| Search | Product Detail |
|--------|---------------|
| ![Search](docs/screenshot-search.png) | ![Detail](docs/screenshot-detail.png) |

| Reviews | Export |
|---------|--------|
| ![Reviews](docs/screenshot-reviews.png) | ![Export](docs/screenshot-export.png) |

## Sample Output

| Product | Price | Rating | Reviews |
|---------|-------|--------|---------|
| Sony WH-CH520 Wireless Headphones | $41.19 | 4.5 | 30,543 |
| Skullcandy Riff Wireless 2 | $27.29 | 4.4 | 10,649 |
| TAGRY Bluetooth Headphones | $35.99 | 4.4 | 83,655 |
| Amazon Basics Bluetooth Headphones | $15.02 | 4.1 | 2,105 |
| Sony ULT WEAR Noise Canceling | $112.72 | 4.3 | 2,921 |

> Full sample data available in [`docs/sample_output.xlsx`](docs/sample_output.xlsx)

## Testing

```bash
# Run all 47 tests
pytest -v

# Lint
ruff check .
```

## Project Structure

```
├── scrapers/
│   ├── base.py              # BrowserManager — stealth Playwright wrapper
│   ├── search.py            # Search results scraper with pagination
│   ├── product_detail.py    # Product detail page scraper (14 fields)
│   └── reviews.py           # Review scraper with date parsing
├── dashboard/
│   └── app.py               # Streamlit dashboard (3 tabs)
├── utils/
│   └── export.py            # CSV, Excel, JSON export utilities
├── tests/
│   ├── fixtures/            # Real Amazon HTML for testing
│   ├── test_base.py         # BrowserManager tests
│   ├── test_search.py       # Search parser tests
│   ├── test_product_detail.py  # Product detail tests (15 assertions)
│   ├── test_reviews.py      # Review parser tests (15 assertions)
│   └── test_export.py       # Export format tests
├── config.py                # Delays, proxy, user-agents
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Tech Stack

- **Scraping:** Playwright (stealth mode), BeautifulSoup4, lxml
- **Data:** Pandas, openpyxl
- **Dashboard:** Streamlit
- **Testing:** pytest (47 tests)
- **Linting:** ruff
- **CI/CD:** GitHub Actions

## Configuration

Edit `config.py` or create a `.env` file (see `.env.example`):

```python
DELAY_RANGE = (2, 5)    # Seconds between requests
MAX_PAGES = 3            # Default page limit
PROXY = None             # "http://user:pass@host:port"
```

## License

MIT — see [LICENSE](LICENSE) for details.

## Disclaimer

This project is for **educational and portfolio purposes**. Amazon's Terms of Service restrict automated access. For production use, consider the [Amazon Product Advertising API](https://webservices.amazon.com/paapi5/documentation/).

---

Built by [@ekremkutukculer](https://github.com/ekremkutukculer)
