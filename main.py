import pandas as pd

from src.config import (
    FORECAST_HORIZON,
    TOP_N_SKUS,
    TEST_SIZE,
    FORECAST_DIR,
    METRICS_DIR,
    REPORTS_DIR,
    SKU_COL,
    DESC_COL,
    DATE_COL,
    SALES_COL,
    STOCK_COL,
)
from src.data_loader import load_excel_data
from src.preprocessing import clean_sales_data, get_top_skus, build_monthly_series
from src.forecasting import choose_and_forecast
from src.evaluation import calculate_metrics
from src.utils import print_header, series_train_test_split
from src.abc_xyz import build_abc_xyz
from src.alerts import build_inventory_decisions


def set_column_widths(worksheet, df):
    for idx, col in enumerate(df.columns):
        if len(df) > 0:
            max_cell_len = df[col].apply(lambda x: len(str(x)) if pd.notna(x) else 0).max()
        else:
            max_cell_len = 0

        max_len = max(len(str(col)), max_cell_len)
        width = min(max(max_len + 2, 10), 28)

        if col in ["DESCRIPCION", "ACTION", "INDICADOR", "VALOR"]:
            width = min(max(max_len + 2, 18), 42)

        if col in ["SKU", "ABC_CLASS", "XYZ_CLASS", "ABC_XYZ", "ALERT_STATUS", "MODEL_USED"]:
            width = min(max(max_len + 2, 12), 20)

        worksheet.set_column(idx, idx, width)


def format_table_sheet(writer, sheet_name, df):
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    header_fmt = workbook.add_format({
        "bold": True,
        "font_color": "white",
        "bg_color": "#1F4E78",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True
    })

    text_fmt = workbook.add_format({
        "border": 1,
        "valign": "top"
    })

    num_fmt = workbook.add_format({
        "border": 1,
        "num_format": "#,##0.00"
    })

    int_fmt = workbook.add_format({
        "border": 1,
        "num_format": "0"
    })

    status_ok_fmt = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100", "border": 1})
    status_reorder_fmt = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500", "border": 1})
    status_critical_fmt = workbook.add_format({"bg_color": "#F4CCCC", "font_color": "#990000", "border": 1})
    status_over_fmt = workbook.add_format({"bg_color": "#D9EAD3", "font_color": "#274E13", "border": 1})
    status_stockout_fmt = workbook.add_format({"bg_color": "#EA9999", "font_color": "#660000", "border": 1})

    rows, cols = df.shape

    worksheet.freeze_panes(1, 0)
    if rows > 0 and cols > 0:
        worksheet.autofilter(0, 0, rows, cols - 1)

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_fmt)

    set_column_widths(worksheet, df)

    number_like_cols = {
        "CURRENT_STOCK", "LAST_MONTH_SALES", "F1", "F2", "F3",
        "FORECAST_3M", "AVG_FORECAST_MONTH", "MONTHS_OF_COVER",
        "SAFETY_STOCK", "REORDER_POINT", "RECOMMENDED_PURCHASE",
        "TOTAL_SALES", "MEAN_MONTHLY_SALES", "STD_MONTHLY_SALES",
        "CV", "SAFETY_FACTOR", "PRIORITY_SCORE", "MAE", "RMSE", "MAPE",
        "FORECAST", "HORIZONTE", "VALOR"
    }

    integer_cols = {"HORIZONTE"}

    for idx, col in enumerate(df.columns):
        if col in integer_cols:
            worksheet.set_column(idx, idx, None, int_fmt)
        elif col in number_like_cols:
            worksheet.set_column(idx, idx, None, num_fmt)
        else:
            worksheet.set_column(idx, idx, None, text_fmt)

    if "ALERT_STATUS" in df.columns and rows > 0:
        col_idx = df.columns.get_loc("ALERT_STATUS")
        worksheet.conditional_format(1, col_idx, rows, col_idx, {
            "type": "text",
            "criteria": "containing",
            "value": "OK",
            "format": status_ok_fmt
        })
        worksheet.conditional_format(1, col_idx, rows, col_idx, {
            "type": "text",
            "criteria": "containing",
            "value": "REORDEN",
            "format": status_reorder_fmt
        })
        worksheet.conditional_format(1, col_idx, rows, col_idx, {
            "type": "text",
            "criteria": "containing",
            "value": "CRITICO",
            "format": status_critical_fmt
        })
        worksheet.conditional_format(1, col_idx, rows, col_idx, {
            "type": "text",
            "criteria": "containing",
            "value": "SIN STOCK",
            "format": status_stockout_fmt
        })
        worksheet.conditional_format(1, col_idx, rows, col_idx, {
            "type": "text",
            "criteria": "containing",
            "value": "SOBREINVENTARIO",
            "format": status_over_fmt
        })


def format_summary_sheet(writer, sheet_name, df):
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    title_fmt = workbook.add_format({
        "bold": True,
        "font_color": "white",
        "bg_color": "#1F4E78",
        "border": 1,
        "align": "center",
        "valign": "vcenter"
    })

    label_fmt = workbook.add_format({
        "border": 1,
        "text_wrap": True
    })

    value_fmt = workbook.add_format({
        "border": 1,
        "num_format": "#,##0.00"
    })

    text_value_fmt = workbook.add_format({
        "border": 1,
        "text_wrap": True
    })

    rows, cols = df.shape
    worksheet.freeze_panes(1, 0)

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, title_fmt)

    worksheet.set_column(0, 0, 38)
    worksheet.set_column(1, 1, 28)

    for row in range(1, rows + 1):
        worksheet.write(row, 0, df.iloc[row - 1, 0], label_fmt)
        val = df.iloc[row - 1, 1]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            worksheet.write(row, 1, val, value_fmt)
        else:
            worksheet.write(row, 1, str(val), text_value_fmt)

    if rows > 0:
        worksheet.autofilter(0, 0, rows, cols - 1)


def main():
    print_header("CARGA DE DATOS")
    sales_df, days_df = load_excel_data()
    sales_df = clean_sales_data(sales_df)

    print(f"Filas ventas: {len(sales_df)}")
    print(f"SKUs unicos: {sales_df[SKU_COL].nunique()}")

    print_header("SELECCION DE TOP SKUS")
    top_skus = get_top_skus(sales_df, TOP_N_SKUS)
    print(f"Top SKUs seleccionados: {len(top_skus)}")

    sales_top = sales_df[sales_df[SKU_COL].isin(top_skus)].copy()

    monthly_records = []
    metrics_results = []
    forecast_results = []
    summary_rows = []

    print_header("PRONOSTICO POR SKU")

    for i, sku in enumerate(top_skus, start=1):
        sku_df = sales_top[sales_top[SKU_COL] == sku].copy()
        description = sku_df[DESC_COL].iloc[0] if DESC_COL in sku_df.columns else ""

        series = build_monthly_series(sales_top, sku)

        for idx, value in series.items():
            monthly_records.append({
                SKU_COL: sku,
                "DATE": idx,
                "MONTHLY_SALES": float(value)
            })

        if len(series) <= TEST_SIZE:
            continue

        train, test = series_train_test_split(series, TEST_SIZE)

        y_pred_test, selected_model = choose_and_forecast(train, TEST_SIZE)
        metric_dict = calculate_metrics(test.values, y_pred_test)

        future_forecast, future_model = choose_and_forecast(series, FORECAST_HORIZON)
        future_forecast = [round(float(x), 2) for x in future_forecast]

        latest_row = sku_df.sort_values(DATE_COL).iloc[-1]
        current_stock = float(pd.to_numeric(latest_row.get(STOCK_COL, 0), errors="coerce"))
        last_sales = float(pd.to_numeric(latest_row.get(SALES_COL, 0), errors="coerce"))

        metrics_results.append({
            "SKU": sku,
            "DESCRIPCION": description,
            "MODELO_TEST": selected_model,
            "MAE": metric_dict["MAE"],
            "RMSE": metric_dict["RMSE"],
            "MAPE": metric_dict["MAPE"]
        })

        for step, value in enumerate(future_forecast, start=1):
            forecast_results.append({
                "SKU": sku,
                "DESCRIPCION": description,
                "MODELO_FORECAST": future_model,
                "HORIZONTE": step,
                "FORECAST": value
            })

        summary_rows.append({
            "SKU": sku,
            "DESCRIPCION": description,
            "CURRENT_STOCK": round(current_stock, 2),
            "LAST_MONTH_SALES": round(last_sales, 2),
            "MODEL_USED": future_model,
            "F1": future_forecast[0] if len(future_forecast) > 0 else 0,
            "F2": future_forecast[1] if len(future_forecast) > 1 else 0,
            "F3": future_forecast[2] if len(future_forecast) > 2 else 0
        })

        print(f"[{i}/{len(top_skus)}] SKU: {sku} | Modelo: {selected_model}")

    monthly_df = pd.DataFrame(monthly_records)
    metrics_df = pd.DataFrame(metrics_results)
    forecast_df = pd.DataFrame(forecast_results)
    summary_df = pd.DataFrame(summary_rows)

    print_header("ABC XYZ")
    abc_xyz_df = build_abc_xyz(sales_top, monthly_df)

    print_header("ALERTAS Y RECOMENDACIONES")
    final_df = (
        summary_df
        .merge(abc_xyz_df, left_on="SKU", right_on=SKU_COL, how="left")
        .drop(columns=[SKU_COL], errors="ignore")
    )

    final_df = build_inventory_decisions(final_df)

    final_df["PRIORITY_SCORE"] = (
        final_df["RECOMMENDED_PURCHASE"].fillna(0)
        * final_df["TOTAL_SALES"].fillna(0).rank(pct=True)
    ).round(2)

    status_order = {
        "SIN STOCK": 1,
        "CRITICO": 2,
        "REORDEN": 3,
        "OK": 4,
        "SOBREINVENTARIO": 5
    }

    alertas_prioridad_df = final_df.copy()
    alertas_prioridad_df["STATUS_ORDER"] = alertas_prioridad_df["ALERT_STATUS"].map(status_order).fillna(99)
    alertas_prioridad_df = alertas_prioridad_df.sort_values(
        by=["STATUS_ORDER", "ABC_CLASS", "PRIORITY_SCORE"],
        ascending=[True, True, False]
    ).drop(columns=["STATUS_ORDER"])

    top_urgentes_df = alertas_prioridad_df[
        alertas_prioridad_df["ALERT_STATUS"].isin(["SIN STOCK", "CRITICO", "REORDEN"])
    ].head(10).copy()

    top_sobreinventario_df = final_df[
        final_df["ALERT_STATUS"] == "SOBREINVENTARIO"
    ].sort_values(
        by=["CURRENT_STOCK", "MONTHS_OF_COVER"],
        ascending=[False, False]
    ).head(10).copy()

    top_compra_df = final_df[
        final_df["RECOMMENDED_PURCHASE"] > 0
    ].sort_values(
        by=["RECOMMENDED_PURCHASE", "PRIORITY_SCORE"],
        ascending=[False, False]
    ).head(10).copy()

    resumen_gerencial_df = pd.DataFrame([
        {"INDICADOR": "SKUs analizados", "VALOR": len(final_df)},
        {"INDICADOR": "SKUs sin stock", "VALOR": int((final_df["ALERT_STATUS"] == "SIN STOCK").sum())},
        {"INDICADOR": "SKUs criticos", "VALOR": int((final_df["ALERT_STATUS"] == "CRITICO").sum())},
        {"INDICADOR": "SKUs en reorden", "VALOR": int((final_df["ALERT_STATUS"] == "REORDEN").sum())},
        {"INDICADOR": "SKUs con sobreinventario", "VALOR": int((final_df["ALERT_STATUS"] == "SOBREINVENTARIO").sum())},
        {"INDICADOR": "SKUs en estado OK", "VALOR": int((final_df["ALERT_STATUS"] == "OK").sum())},
        {"INDICADOR": "Compra total recomendada", "VALOR": round(final_df["RECOMMENDED_PURCHASE"].sum(), 2)},
        {"INDICADOR": "Stock total actual", "VALOR": round(final_df["CURRENT_STOCK"].sum(), 2)},
        {"INDICADOR": "Pronostico total 3 meses", "VALOR": round(final_df["FORECAST_3M"].sum(), 2)},
        {
            "INDICADOR": "Observacion principal",
            "VALOR": (
                "Predomina el sobreinventario en los SKUs analizados, "
                "por lo que la oportunidad principal esta en optimizar politicas de compra "
                "y reducir exceso de stock, mas que en compras urgentes."
            )
        }
    ])

    ordered_columns = [
        "SKU", "DESCRIPCION", "ABC_CLASS", "XYZ_CLASS", "ABC_XYZ",
        "CURRENT_STOCK", "LAST_MONTH_SALES", "F1", "F2", "F3",
        "FORECAST_3M", "AVG_FORECAST_MONTH", "MONTHS_OF_COVER",
        "SAFETY_STOCK", "REORDER_POINT", "RECOMMENDED_PURCHASE",
        "ALERT_STATUS", "ACTION", "MODEL_USED", "TOTAL_SALES",
        "MEAN_MONTHLY_SALES", "STD_MONTHLY_SALES", "CV",
        "SAFETY_FACTOR", "PRIORITY_SCORE",
    ]

    final_df = final_df[[col for col in ordered_columns if col in final_df.columns]]
    alertas_prioridad_df = alertas_prioridad_df[[col for col in ordered_columns if col in alertas_prioridad_df.columns]]
    top_urgentes_df = top_urgentes_df[[col for col in ordered_columns if col in top_urgentes_df.columns]]
    top_sobreinventario_df = top_sobreinventario_df[[col for col in ordered_columns if col in top_sobreinventario_df.columns]]
    top_compra_df = top_compra_df[[col for col in ordered_columns if col in top_compra_df.columns]]

    metrics_path = METRICS_DIR / "metrics_top50.csv"
    forecast_path = FORECAST_DIR / "forecast_top50.csv"
    abc_xyz_path = REPORTS_DIR / "abc_xyz_top50.csv"
    decisions_path = REPORTS_DIR / "inventory_decisions_top50.csv"
    excel_report_path = REPORTS_DIR / "inventory_decision_support.xlsx"

    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    forecast_df.to_csv(forecast_path, index=False, encoding="utf-8-sig")
    abc_xyz_df.to_csv(abc_xyz_path, index=False, encoding="utf-8-sig")
    final_df.to_csv(decisions_path, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(excel_report_path, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, sheet_name="Resumen_Ejecutivo", index=False)
        alertas_prioridad_df.to_excel(writer, sheet_name="Alertas_Prioridad", index=False)
        resumen_gerencial_df.to_excel(writer, sheet_name="Resumen_Gerencial", index=False)
        top_urgentes_df.to_excel(writer, sheet_name="Top_10_Urgentes", index=False)
        top_sobreinventario_df.to_excel(writer, sheet_name="Top_10_Sobreinventario", index=False)
        top_compra_df.to_excel(writer, sheet_name="Top_10_Compra", index=False)
        metrics_df.to_excel(writer, sheet_name="Metricas_Top50", index=False)
        forecast_df.to_excel(writer, sheet_name="Pronosticos_Top50", index=False)
        abc_xyz_df.to_excel(writer, sheet_name="ABC_XYZ", index=False)
        monthly_df.to_excel(writer, sheet_name="Series_Mensuales", index=False)

        format_table_sheet(writer, "Resumen_Ejecutivo", final_df)
        format_table_sheet(writer, "Alertas_Prioridad", alertas_prioridad_df)
        format_summary_sheet(writer, "Resumen_Gerencial", resumen_gerencial_df)
        format_table_sheet(writer, "Top_10_Urgentes", top_urgentes_df)
        format_table_sheet(writer, "Top_10_Sobreinventario", top_sobreinventario_df)
        format_table_sheet(writer, "Top_10_Compra", top_compra_df)
        format_table_sheet(writer, "Metricas_Top50", metrics_df)
        format_table_sheet(writer, "Pronosticos_Top50", forecast_df)
        format_table_sheet(writer, "ABC_XYZ", abc_xyz_df)
        format_table_sheet(writer, "Series_Mensuales", monthly_df)

    print_header("RESULTADOS EXPORTADOS")
    print(f"Metricas CSV: {metrics_path}")
    print(f"Pronosticos CSV: {forecast_path}")
    print(f"ABC_XYZ CSV: {abc_xyz_path}")
    print(f"Decisiones CSV: {decisions_path}")
    print(f"Excel final: {excel_report_path}")


if __name__ == "__main__":
    main()

