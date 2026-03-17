import json
from typing import Any

import pandas as pd


def _to_dataframe(data: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(data)


def export_csv(data: list[dict[str, Any]], filepath: str) -> None:
    """Export data to CSV with UTF-8-sig encoding."""
    df = _to_dataframe(data)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")


def export_excel(data: list[dict[str, Any]], filepath: str) -> None:
    """Export data to a single-sheet Excel file."""
    df = _to_dataframe(data)
    df.to_excel(filepath, index=False, engine="openpyxl")


def export_json(data: list[dict[str, Any]], filepath: str) -> None:
    """Export data to a JSON file with unicode support."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_multi_sheet_excel(
    search_data: list[dict[str, Any]],
    detail_data: list[dict[str, Any]],
    review_data: list[dict[str, Any]],
    filepath: str,
) -> None:
    """Export search, detail, and review data to a 3-sheet Excel workbook."""
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        if search_data:
            pd.DataFrame(search_data).to_excel(writer, sheet_name="Search Results", index=False)
        if detail_data:
            pd.DataFrame(detail_data).to_excel(writer, sheet_name="Product Details", index=False)
        if review_data:
            pd.DataFrame(review_data).to_excel(writer, sheet_name="Reviews", index=False)
