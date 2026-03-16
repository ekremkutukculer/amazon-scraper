import asyncio
import sys
import os

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.ecommerce_scraper import scrape_amazon
from utils.export import export_csv
from config import DATA_DIR

st.set_page_config(page_title="Amazon Scraper Dashboard", page_icon="🛒", layout="wide")
st.title("Amazon Product Scraper")
st.markdown("---")

# --- Sidebar: Scrape Controls ---
with st.sidebar:
    st.header("Scrape Settings")
    search_term = st.text_input("Search Term", placeholder="e.g. wireless headphones")
    max_pages = st.slider("Max Pages", 1, 10, 3)
    scrape_btn = st.button("Start Scraping", type="primary", use_container_width=True)

# --- Scrape Execution ---
if scrape_btn and search_term:
    with st.spinner(f"Scraping Amazon for '{search_term}'..."):
        products = scrape_amazon(search_term, max_pages=max_pages)

    if products:
        df = pd.DataFrame(products)
        os.makedirs(DATA_DIR, exist_ok=True)
        safe_term = search_term.replace(" ", "_")[:30]
        csv_path = os.path.join(DATA_DIR, f"{safe_term}.csv")
        export_csv(products, csv_path)
        st.session_state["df"] = df
        st.session_state["products"] = products
        st.success(f"{len(products)} products scraped and saved!")
    else:
        st.warning("No products found. Amazon may be blocking requests.")

# --- Display Data ---
if "df" in st.session_state:
    df = st.session_state["df"]

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", len(df))
    col2.metric("Avg Price", f"${df['price'].mean():.2f}" if df["price"].notna().any() else "N/A")
    col3.metric("Avg Rating", f"{df['rating'].mean():.1f}" if df["rating"].notna().any() else "N/A")
    col4.metric("With Reviews", df["reviews"].notna().sum())

    st.markdown("---")

    # Data table
    st.subheader("Product Data")
    st.dataframe(df, use_container_width=True, height=400)

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Price Distribution")
        price_data = df["price"].dropna()
        if not price_data.empty:
            st.bar_chart(price_data.value_counts(bins=20).sort_index())

    with chart_col2:
        st.subheader("Rating Distribution")
        rating_data = df["rating"].dropna()
        if not rating_data.empty:
            st.bar_chart(rating_data.value_counts().sort_index())

    st.markdown("---")

    # Export buttons
    st.subheader("Export Data")
    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV", csv_data, "amazon_products.csv", "text/csv", use_container_width=True)

    with exp_col2:
        from io import BytesIO
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button("Download Excel", buffer.getvalue(), "amazon_products.xlsx", use_container_width=True)

    with exp_col3:
        json_data = df.to_json(orient="records", force_ascii=False, indent=2)
        st.download_button("Download JSON", json_data, "amazon_products.json", "application/json", use_container_width=True)

else:
    st.info("Enter a search term in the sidebar and click 'Start Scraping' to begin.")
