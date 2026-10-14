"""Очистка и нормализация данных."""
import pandas as pd


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["seller_id"])
    df["seller_zip_code_prefix"] = pd.to_numeric(
        df["seller_zip_code_prefix"], errors="coerce"
    ).astype("Int64")
    df["seller_city"] = df["seller_city"].str.strip().str.lower()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    df = df.dropna(subset=["seller_id", "seller_state"])
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["order_id"])

    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    numeric_cols = ["items_price", "freight_value", "order_total", "review_score"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # Фильтр: оставляем только валидные заказы
    df = df[df["order_total"].notna() & (df["order_total"] > 0)]

    return df