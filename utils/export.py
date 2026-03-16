import json
import pandas as pd


def _to_dataframe(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)


def export_csv(data: list[dict], filepath: str) -> None:
    df = _to_dataframe(data)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")


def export_excel(data: list[dict], filepath: str) -> None:
    df = _to_dataframe(data)
    df.to_excel(filepath, index=False, engine="openpyxl")


def export_json(data: list[dict], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
