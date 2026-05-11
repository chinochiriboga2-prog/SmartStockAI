import pandas as pd

def calculate_safety_factor(abc_class: str, xyz_class: str) -> float:
    abc_factor = {"A": 1.2, "B": 1.0, "C": 0.8}.get(abc_class, 1.0)
    xyz_factor = {"X": 0.8, "Y": 1.0, "Z": 1.2}.get(xyz_class, 1.0)
    return abc_factor * xyz_factor

def build_inventory_decisions(summary_df: pd.DataFrame) -> pd.DataFrame:
    df = summary_df.copy()

    numeric_cols = ["CURRENT_STOCK", "F1", "F2", "F3"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["FORECAST_3M"] = (df["F1"] + df["F2"] + df["F3"]).round(2)
    df["AVG_FORECAST_MONTH"] = (df["FORECAST_3M"] / 3.0).round(2)

    df["SAFETY_FACTOR"] = df.apply(
        lambda row: calculate_safety_factor(row.get("ABC_CLASS"), row.get("XYZ_CLASS")),
        axis=1
    )

    df["SAFETY_STOCK"] = (df["AVG_FORECAST_MONTH"] * df["SAFETY_FACTOR"]).round(2)
    df["REORDER_POINT"] = (df["AVG_FORECAST_MONTH"] + df["SAFETY_STOCK"]).round(2)

    df["MONTHS_OF_COVER"] = df.apply(
        lambda row: round(row["CURRENT_STOCK"] / row["AVG_FORECAST_MONTH"], 2)
        if row["AVG_FORECAST_MONTH"] > 0 else None,
        axis=1
    )

    df["RECOMMENDED_PURCHASE"] = (
        df["REORDER_POINT"] + df["AVG_FORECAST_MONTH"] - df["CURRENT_STOCK"]
    ).clip(lower=0).round(2)

    def stock_status(row):
        stock = row["CURRENT_STOCK"]
        avg = row["AVG_FORECAST_MONTH"]
        cover = row["MONTHS_OF_COVER"]

        if stock <= 0:
            return "SIN STOCK"
        if avg <= 0:
            return "OK"
        if cover is not None and cover < 0.5:
            return "CRITICO"
        if cover is not None and cover < 1.5:
            return "REORDEN"
        if cover is not None and cover > 4:
            return "SOBREINVENTARIO"
        return "OK"

    df["ALERT_STATUS"] = df.apply(stock_status, axis=1)

    def action_text(row):
        status = row["ALERT_STATUS"]
        qty = row["RECOMMENDED_PURCHASE"]

        if status == "SIN STOCK":
            return f"Comprar urgente: {qty:.0f} unidades"
        if status == "CRITICO":
            return f"Comprar urgente: {qty:.0f} unidades"
        if status == "REORDEN":
            return f"Reponer: {qty:.0f} unidades"
        if status == "SOBREINVENTARIO":
            return "Revisar compras; posible sobrestock"
        return "Sin accion inmediata"

    df["ACTION"] = df.apply(action_text, axis=1)

    return df
