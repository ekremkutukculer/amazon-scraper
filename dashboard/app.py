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

# --- Custom CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stMetric { background: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9900; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    .product-img { width: 50px; height: 50px; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

st.title("Amazon Product Scraper")
st.caption("Real-time product data extraction with price analysis")
st.markdown("---")

# --- Sidebar: Scrape Controls ---
with st.sidebar:
    st.header("Scrape Settings")
    search_term = st.text_input("Search Term", placeholder="e.g. wireless headphones")
    max_pages = st.slider("Max Pages", 1, 10, 3)
    scrape_btn = st.button("Start Scraping", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**Filters** (apply after scraping)")
    price_range = st.slider("Price Range ($)", 0.0, 1000.0, (0.0, 1000.0), step=5.0)
    min_rating = st.slider("Min Rating", 0.0, 5.0, 0.0, step=0.5)
    min_reviews = st.number_input("Min Reviews", min_value=0, value=0, step=10)

# --- Scrape Execution ---
if scrape_btn and search_term:
    progress_bar = st.progress(0, text="Starting scraper...")
    with st.spinner(f"Scraping Amazon for '{search_term}'..."):
        products = scrape_amazon(search_term, max_pages=max_pages)
        progress_bar.progress(100, text="Done!")

    if products:
        df = pd.DataFrame(products)
        os.makedirs(DATA_DIR, exist_ok=True)
        safe_term = search_term.replace(" ", "_")[:30]
        csv_path = os.path.join(DATA_DIR, f"{safe_term}.csv")
        export_csv(products, csv_path)
        st.session_state["df"] = df
        st.session_state["products"] = products
        st.session_state["search_term"] = search_term
        st.success(f"{len(products)} products scraped and saved!")
    else:
        st.warning("No products found. Amazon may be blocking requests or showing a CAPTCHA.")

# --- Display Data ---
if "df" in st.session_state:
    df = st.session_state["df"].copy()

    # Apply filters
    if df["price"].notna().any():
        df = df[
            (df["price"].isna()) | ((df["price"] >= price_range[0]) & (df["price"] <= price_range[1]))
        ]
    if df["rating"].notna().any():
        df = df[(df["rating"].isna()) | (df["rating"] >= min_rating)]
    if df["reviews"].notna().any():
        df = df[(df["reviews"].isna()) | (df["reviews"] >= min_reviews)]

    # --- Metrics Row ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Products", len(df))
    col2.metric("Avg Price", f"${df['price'].mean():,.2f}" if df["price"].notna().any() else "N/A")
    col3.metric("Avg Rating", f"{df['rating'].mean():.1f} / 5" if df["rating"].notna().any() else "N/A")
    col4.metric("Total Reviews", f"{df['reviews'].sum():,.0f}" if df["reviews"].notna().any() else "N/A")
    badges = df["badge"].notna().sum() if "badge" in df.columns else 0
    col5.metric("Badged Products", badges)

    st.markdown("---")

    # --- Charts Row ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Price Distribution")
        price_data = df["price"].dropna()
        if not price_data.empty:
            import numpy as np
            bins = np.linspace(price_data.min(), price_data.max(), 15)
            hist_data = pd.cut(price_data, bins=bins).value_counts().sort_index()
            hist_data.index = [f"${int(i.left)}-{int(i.right)}" for i in hist_data.index]
            st.bar_chart(hist_data)

    with chart_col2:
        st.subheader("Rating Distribution")
        rating_data = df["rating"].dropna()
        if not rating_data.empty:
            rating_counts = rating_data.round(1).value_counts().sort_index()
            st.bar_chart(rating_counts)

    # --- Scatter: Price vs Rating ---
    st.subheader("Price vs Rating")
    scatter_df = df.dropna(subset=["price", "rating"])
    if not scatter_df.empty:
        st.scatter_chart(scatter_df, x="price", y="rating", size="reviews")

    st.markdown("---")

    # --- Top Tables ---
    top_col1, top_col2 = st.columns(2)

    with top_col1:
        st.subheader("Top 5 Best Value (Rating/Price)")
        value_df = df.dropna(subset=["price", "rating"]).copy()
        if not value_df.empty:
            value_df["value_score"] = value_df["rating"] / value_df["price"] * 100
            top_value = value_df.nlargest(5, "value_score")[["name", "price", "rating", "reviews"]]
            top_value["name"] = top_value["name"].str[:50]
            st.dataframe(top_value, use_container_width=True, hide_index=True)

    with top_col2:
        st.subheader("Top 5 Most Reviewed")
        if df["reviews"].notna().any():
            top_reviews = df.nlargest(5, "reviews")[["name", "price", "rating", "reviews"]]
            top_reviews["name"] = top_reviews["name"].str[:50]
            st.dataframe(top_reviews, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Brand Analysis ---
    if "brand" in df.columns and df["brand"].notna().any():
        st.subheader("Brand Analysis")
        brand_col1, brand_col2 = st.columns(2)

        brand_stats = df.groupby("brand").agg(
            count=("name", "count"),
            avg_price=("price", "mean"),
            avg_rating=("rating", "mean"),
        ).round(2)

        with brand_col1:
            st.markdown("**Top Brands by Product Count**")
            top_brands = brand_stats.nlargest(10, "count")
            st.bar_chart(top_brands["count"])

        with brand_col2:
            st.markdown("**Brand Price Comparison**")
            top_brand_prices = brand_stats.nlargest(10, "count")["avg_price"]
            st.bar_chart(top_brand_prices)

    st.markdown("---")

    # --- Full Data Table ---
    st.subheader("All Products")
    display_cols = ["name", "price", "rating", "reviews", "brand", "badge", "asin"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(
        df[available_cols],
        use_container_width=True,
        height=400,
        column_config={
            "name": st.column_config.TextColumn("Product", width="large"),
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "rating": st.column_config.NumberColumn("Rating", format="%.1f ⭐"),
            "reviews": st.column_config.NumberColumn("Reviews", format="%d"),
            "brand": st.column_config.TextColumn("Brand"),
            "badge": st.column_config.TextColumn("Badge"),
            "asin": st.column_config.TextColumn("ASIN", width="small"),
        },
        hide_index=True,
    )

    st.markdown("---")

    # --- Export ---
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
