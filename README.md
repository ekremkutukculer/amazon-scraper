# Amazon Product Scraper

A Python-based Amazon product scraper with an interactive Streamlit dashboard. Scrapes product data from Amazon search results and visualizes it with charts and export options.

## Features

- **Amazon Search Scraping** — Extract product name, price, rating, reviews, and stock status
- **Anti-Bot Protection** — User-Agent rotation, random delays, retry with exponential backoff
- **Interactive Dashboard** — Filter, sort, and explore scraped data
- **Data Export** — Download results as CSV, Excel, or JSON
- **Proxy Support** — Optional proxy configuration for large-scale scraping

## Screenshots

> _Add screenshots of the dashboard here_

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd proje1

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run dashboard/app.py
```

## Usage

1. Open the dashboard in your browser
2. Enter a search term (e.g., "wireless headphones")
3. Set the number of pages to scrape
4. Click "Start Scraping"
5. View results in the table and charts
6. Export data in your preferred format

## Configuration

Edit `config.py` to customize:

```python
DELAY_RANGE = (2, 5)    # Seconds between requests
MAX_PAGES = 3            # Default page limit
PROXY = None             # Your proxy URL
```

## Tech Stack

- Python 3.10+
- httpx + BeautifulSoup4
- Pandas
- Streamlit
- openpyxl

## Disclaimer

This project is for educational and portfolio purposes only. Amazon's Terms of Service prohibit scraping. For production use, consider the [Amazon Product Advertising API](https://webservices.amazon.com/paapi5/documentation/).
