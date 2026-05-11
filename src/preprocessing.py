import pandas as pd
from src.config import DATE_COL, SKU_COL, SALES_COL, STOCK_COL

def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [col.strip() for col in df.columns]

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df[SALES_COL] = pd.to_numeric(df[SALES_COL], errors="coerce").fillna(0)
    df[STOCK_COL] = pd.to_numeric(df[STOCK_COL], errors="coerce").fillna(0)

    df = df.dropna(subset=[SKU_COL, DATE_COL])
    df = df.sort_values([SKU_COL, DATE_COL])

    return df

def get_top_skus(df: pd.DataFrame, top_n: int = 50):
    ranking = (
        df.groupby(SKU_COL)[SALES_COL]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index
        .tolist()
    )
    return ranking

def build_monthly_series(df: pd.DataFrame, sku: str) -> pd.Series:
    sku_df = df[df[SKU_COL] == sku].copy()
    sku_df = sku_df.sort_values(DATE_COL)

    series = (
        sku_df.set_index(DATE_COL)[SALES_COL]
        .asfreq("MS")
        .fillna(0)
    )

    return series
