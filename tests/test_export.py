import json
import pandas as pd
from utils.export import export_csv, export_excel, export_json

SAMPLE_DATA = [
    {"name": "Product A", "price": 29.99, "rating": 4.5, "reviews": 100, "stock": "In Stock", "asin": "B001"},
    {"name": "Product B", "price": None, "rating": 3.0, "reviews": 50, "stock": None, "asin": "B002"},
]


def test_export_csv(tmp_path):
    filepath = tmp_path / "test.csv"
    export_csv(SAMPLE_DATA, str(filepath))
    assert filepath.exists()
    df = pd.read_csv(filepath)
    assert len(df) == 2
    assert df.iloc[0]["name"] == "Product A"


def test_export_excel(tmp_path):
    filepath = tmp_path / "test.xlsx"
    export_excel(SAMPLE_DATA, str(filepath))
    assert filepath.exists()
    df = pd.read_excel(filepath)
    assert len(df) == 2


def test_export_json(tmp_path):
    filepath = tmp_path / "test.json"
    export_json(SAMPLE_DATA, str(filepath))
    assert filepath.exists()
    with open(filepath) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["name"] == "Product A"
