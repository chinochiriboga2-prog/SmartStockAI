import numpy as np
import pandas as pd
from src.config import SKU_COL, SALES_COL

def classify_abc(df: pd.DataFrame) -> pd.DataFrame:
    abc_df = (
        df.groupby(SKU_COL, as_index=False)[SALES_COL]
        .sum()
        .rename(columns={SALES_COL: "TOTAL_SALES"})
        .sort_values("TOTAL_SALES", ascending=False)
    )

    total_sales_sum = abc_df["TOTAL_SALES"].sum()
    if total_sales_sum == 0:
        abc_df["CUM_SHARE"] = 0
    else:
        abc_df["CUM_SHARE"] = abc_df["TOTAL_SALES"].cumsum() / total_sales_sum

    def assign_abc(cum_share):
        if cum_share <= 0.80:
            return "A"
        elif cum_share <= 0.95:
            return "B"
        return "C"

    abc_df["ABC_CLASS"] = abc_df["CUM_SHARE"].apply(assign_abc)
    return abc_df[[SKU_COL, "TOTAL_SALES", "ABC_CLASS"]]

def classify_xyz(series_df: pd.DataFrame) -> pd.DataFrame:
    records = []

    for sku, group in series_df.groupby(SKU_COL):
        values = group["MONTHLY_SALES"].astype(float)
        mean_val = values.mean()
        std_val = values.std(ddof=0)

        if mean_val == 0:
            cv = np.inf if std_val > 0 else 0
        else:
            cv = std_val / mean_val

        if cv <= 0.5:
            xyz = "X"
        elif cv <= 1.0:
            xyz = "Y"
        else:
            xyz = "Z"

        records.append({
            SKU_COL: sku,
            "MEAN_MONTHLY_SALES": round(mean_val, 4),
            "STD_MONTHLY_SALES": round(std_val, 4),
            "CV": round(cv, 4) if np.isfinite(cv) else None,
            "XYZ_CLASS": xyz
        })

    return pd.DataFrame(records)

def build_abc_xyz(df: pd.DataFrame, monthly_df: pd.DataFrame) -> pd.DataFrame:
    abc_df = classify_abc(df)
    xyz_df = classify_xyz(monthly_df)

    merged = abc_df.merge(xyz_df, on=SKU_COL, how="left")
    merged["ABC_XYZ"] = merged["ABC_CLASS"].fillna("") + merged["XYZ_CLASS"].fillna("")
    return merged
