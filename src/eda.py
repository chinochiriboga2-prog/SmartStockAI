from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.config import (
    EXCEL_FILE,
    SALES_SHEET,
    DAYS_SHEET,
    DATE_COL,
    SKU_COL,
    DESC_COL,
    SALES_COL,
    STOCK_COL,
    REPORTS_DIR,
)
from src.preprocessing import clean_sales_data


EDA_DIR = REPORTS_DIR / "eda"
EDA_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# CARGA Y LIMPIEZA
# -----------------------------
def load_data():
    sales_df = pd.read_excel(EXCEL_FILE, sheet_name=SALES_SHEET)
    days_df = pd.read_excel(EXCEL_FILE, sheet_name=DAYS_SHEET)
    sales_df = clean_sales_data(sales_df)
    return sales_df, days_df


def aggregate_monthly_sales(sales_df: pd.DataFrame):
    original_rows = len(sales_df)

    grouped = (
        sales_df.groupby([SKU_COL, DESC_COL, DATE_COL], as_index=False)
        .agg({
            SALES_COL: "sum",
            STOCK_COL: "last"
        })
        .sort_values([SKU_COL, DATE_COL])
    )

    deduplicated_rows = len(grouped)
    duplicate_rows_removed = original_rows - deduplicated_rows

    return grouped, original_rows, deduplicated_rows, duplicate_rows_removed


def build_complete_sku_month_grid(df: pd.DataFrame):
    all_records = []

    for sku, g in df.groupby(SKU_COL):
        g = g.sort_values(DATE_COL).copy()
        desc = g[DESC_COL].iloc[0]

        full_dates = pd.date_range(
            start=g[DATE_COL].min(),
            end=g[DATE_COL].max(),
            freq="MS"
        )

        base = pd.DataFrame({
            DATE_COL: full_dates
        })
        base[SKU_COL] = sku
        base[DESC_COL] = desc

        merged = base.merge(
            g[[SKU_COL, DESC_COL, DATE_COL, SALES_COL, STOCK_COL]],
            on=[SKU_COL, DESC_COL, DATE_COL],
            how="left"
        )

        merged["had_original_record"] = merged[SALES_COL].notna().astype(int)
        merged[SALES_COL] = merged[SALES_COL].fillna(0)
        merged[STOCK_COL] = merged[STOCK_COL].ffill().fillna(0)

        merged["record_type"] = np.where(
            (merged["had_original_record"] == 1) & (merged[SALES_COL] == 0),
            "demanda_cero_registrada",
            np.where(
                merged["had_original_record"] == 0,
                "falta_registro_imputada_cero",
                "venta_observada"
            )
        )

        all_records.append(merged)

    full_df = pd.concat(all_records, ignore_index=True)
    return full_df


# -----------------------------
# TOP 50 Y ABC/XYZ
# -----------------------------
def compute_top50(df: pd.DataFrame):
    ranking = (
        df.groupby([SKU_COL, DESC_COL], as_index=False)[SALES_COL]
        .sum()
        .rename(columns={SALES_COL: "TOTAL_SALES"})
        .sort_values("TOTAL_SALES", ascending=False)
        .reset_index(drop=True)
    )

    ranking["RANK"] = ranking.index + 1
    total_sales = ranking["TOTAL_SALES"].sum()
    ranking["CUM_SALES"] = ranking["TOTAL_SALES"].cumsum()
    ranking["CUM_SHARE"] = ranking["CUM_SALES"] / total_sales if total_sales > 0 else 0

    top50 = ranking.head(50).copy()
    return ranking, top50


def classify_abc(df: pd.DataFrame):
    abc = (
        df.groupby([SKU_COL, DESC_COL], as_index=False)[SALES_COL]
        .sum()
        .rename(columns={SALES_COL: "TOTAL_SALES"})
        .sort_values("TOTAL_SALES", ascending=False)
    )

    total = abc["TOTAL_SALES"].sum()
    abc["CUM_SHARE"] = abc["TOTAL_SALES"].cumsum() / total if total > 0 else 0

    def assign_abc(x):
        if x <= 0.80:
            return "A"
        elif x <= 0.95:
            return "B"
        return "C"

    abc["ABC_CLASS"] = abc["CUM_SHARE"].apply(assign_abc)
    return abc


def classify_xyz(df: pd.DataFrame):
    rows = []
    for sku, g in df.groupby(SKU_COL):
        desc = g[DESC_COL].iloc[0]
        series = g.sort_values(DATE_COL)[SALES_COL].astype(float)

        mean_val = series.mean()
        std_val = series.std(ddof=0)

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

        rows.append({
            SKU_COL: sku,
            DESC_COL: desc,
            "MEAN_MONTHLY_SALES": round(mean_val, 4),
            "STD_MONTHLY_SALES": round(std_val, 4),
            "CV": None if not np.isfinite(cv) else round(cv, 4),
            "XYZ_CLASS": xyz
        })

    return pd.DataFrame(rows)


def build_abc_xyz(df: pd.DataFrame):
    abc = classify_abc(df)
    xyz = classify_xyz(df)

    merged = abc.merge(xyz, on=[SKU_COL, DESC_COL], how="left")
    merged["ABC_XYZ"] = merged["ABC_CLASS"] + merged["XYZ_CLASS"]
    return merged


# -----------------------------
# DEMANDA INTERMITENTE
# -----------------------------
def compute_intermittency(df: pd.DataFrame):
    rows = []

    for sku, g in df.groupby(SKU_COL):
        desc = g[DESC_COL].iloc[0]
        s = g.sort_values(DATE_COL)[SALES_COL].astype(float).values

        n = len(s)
        non_zero = np.sum(s > 0)
        p_non_zero = non_zero / n if n > 0 else 0

        if non_zero > 0:
            adi = n / non_zero
        else:
            adi = np.inf

        mean_ = np.mean(s)
        std_ = np.std(s, ddof=0)

        if mean_ == 0:
            cv2 = np.inf
        else:
            cv2 = (std_ / mean_) ** 2

        if adi < 1.32 and cv2 < 0.49:
            demand_type = "Smooth"
        elif adi >= 1.32 and cv2 < 0.49:
            demand_type = "Intermittent"
        elif adi < 1.32 and cv2 >= 0.49:
            demand_type = "Erratic"
        else:
            demand_type = "Lumpy"

        rows.append({
            SKU_COL: sku,
            DESC_COL: desc,
            "N_PERIODS": n,
            "NON_ZERO_PERIODS": int(non_zero),
            "PCT_NON_ZERO": round(p_non_zero, 4),
            "ADI": None if not np.isfinite(adi) else round(adi, 4),
            "CV2": None if not np.isfinite(cv2) else round(cv2, 4),
            "DEMAND_TYPE": demand_type
        })

    return pd.DataFrame(rows)


# -----------------------------
# BASELINE OPERATIVA
# -----------------------------
def compute_operational_baseline(df: pd.DataFrame):
    baseline_rows = []

    for sku, g in df.groupby(SKU_COL):
        desc = g[DESC_COL].iloc[0]
        g = g.sort_values(DATE_COL).copy()

        periods = len(g)
        stockout_periods = int((g[STOCK_COL] <= 0).sum())
        stockout_rate = stockout_periods / periods if periods > 0 else 0

        g["inventory_days_proxy"] = np.where(
            g[SALES_COL] > 0,
            30 * (g[STOCK_COL] / g[SALES_COL]),
            np.nan
        )

        avg_inventory_days = g["inventory_days_proxy"].replace([np.inf, -np.inf], np.nan).mean()
        service_level_proxy = 1 - stockout_rate

        baseline_rows.append({
            SKU_COL: sku,
            DESC_COL: desc,
            "MONTHS_ANALYZED": periods,
            "STOCKOUT_MONTHS": stockout_periods,
            "STOCKOUT_RATE": round(stockout_rate, 4),
            "AVG_INVENTORY_DAYS_PROXY": round(avg_inventory_days, 2) if pd.notna(avg_inventory_days) else None,
            "SERVICE_LEVEL_PROXY": round(service_level_proxy, 4)
        })

    return pd.DataFrame(baseline_rows)


def compute_inventory_turnover_proxy(full_df: pd.DataFrame):
    rows = []

    for sku, g in full_df.groupby(SKU_COL):
        desc = g[DESC_COL].iloc[0]
        avg_sales = g[SALES_COL].mean()
        avg_stock = g[STOCK_COL].mean()

        turnover = avg_sales / avg_stock if avg_stock > 0 else np.nan

        rows.append({
            SKU_COL: sku,
            DESC_COL: desc,
            "AVG_MONTHLY_SALES": round(avg_sales, 4),
            "AVG_STOCK": round(avg_stock, 4),
            "INVENTORY_TURNOVER_PROXY": round(turnover, 6) if pd.notna(turnover) else None
        })

    return pd.DataFrame(rows)


# -----------------------------
# DISPONIBILIDAD DE VARIABLES CRÍTICAS
# -----------------------------
def assess_critical_variables(days_df: pd.DataFrame):
    lead_time_candidates = [c for c in days_df.columns if "lead" in c.lower() or "import" in c.lower()]
    unit_cost_candidates = [c for c in days_df.columns if "costo" in c.lower() or "cost" in c.lower() or "unitario" in c.lower()]
    safety_stock_candidates = [c for c in days_df.columns if "safety" in c.lower() or "seguridad" in c.lower()]

    assessment = pd.DataFrame([
        {
            "VARIABLE_CRITICA": "Lead Time",
            "DISPONIBLE_EN_FUENTE": "Sí" if len(lead_time_candidates) > 0 else "No",
            "COLUMNAS_POTENCIALES": ", ".join(lead_time_candidates) if lead_time_candidates else "No identificada"
        },
        {
            "VARIABLE_CRITICA": "Costos Unitarios",
            "DISPONIBLE_EN_FUENTE": "Sí" if len(unit_cost_candidates) > 0 else "No",
            "COLUMNAS_POTENCIALES": ", ".join(unit_cost_candidates) if unit_cost_candidates else "No identificada"
        },
        {
            "VARIABLE_CRITICA": "Stock de Seguridad",
            "DISPONIBLE_EN_FUENTE": "Sí" if len(safety_stock_candidates) > 0 else "No",
            "COLUMNAS_POTENCIALES": ", ".join(safety_stock_candidates) if safety_stock_candidates else "No identificada"
        },
    ])

    return assessment


# -----------------------------
# DICCIONARIO DE DATOS
# -----------------------------
def build_data_dictionary():
    rows = [
        ["REFERENCIA", "Identificador único del SKU", "Original", "Texto", "Hoja INFORME-VENTAS"],
        ["DESCRIPCIÓN", "Descripción comercial del SKU", "Original", "Texto", "Hoja INFORME-VENTAS"],
        ["FECHA", "Fecha de observación mensual", "Original", "Fecha", "Hoja INFORME-VENTAS"],
        ["VENTAS", "Cantidad vendida del SKU en el periodo", "Original", "Numérico", "Hoja INFORME-VENTAS"],
        ["STOCK", "Stock disponible registrado en el periodo", "Original", "Numérico", "Hoja INFORME-VENTAS"],
        ["record_type", "Clasificación del registro: venta observada, demanda cero registrada o falta de registro imputada a cero", "Derivada", "Categoría", "EDA"],
        ["TOTAL_SALES", "Ventas acumuladas del SKU en todo el histórico", "Derivada", "Numérico", "EDA"],
        ["ABC_CLASS", "Clasificación ABC según peso acumulado en ventas", "Derivada", "Categoría", "EDA"],
        ["XYZ_CLASS", "Clasificación XYZ según variabilidad de la demanda", "Derivada", "Categoría", "EDA"],
        ["ABC_XYZ", "Combinación de clasificaciones ABC y XYZ", "Derivada", "Categoría", "EDA"],
        ["MEAN_MONTHLY_SALES", "Promedio mensual de ventas por SKU", "Derivada", "Numérico", "EDA"],
        ["STD_MONTHLY_SALES", "Desviación estándar mensual de ventas por SKU", "Derivada", "Numérico", "EDA"],
        ["CV", "Coeficiente de variación de ventas", "Derivada", "Numérico", "EDA"],
        ["ADI", "Average Demand Interval, proxy de intermitencia", "Derivada", "Numérico", "EDA"],
        ["CV2", "Cuadrado del coeficiente de variación", "Derivada", "Numérico", "EDA"],
        ["DEMAND_TYPE", "Tipo de demanda: Smooth, Intermittent, Erratic o Lumpy", "Derivada", "Categoría", "EDA"],
        ["STOCKOUT_RATE", "Frecuencia mensual proxy de quiebres de stock", "Derivada", "Numérico", "EDA"],
        ["AVG_INVENTORY_DAYS_PROXY", "Días de inventario aproximados con base en ventas mensuales", "Derivada", "Numérico", "EDA"],
        ["SERVICE_LEVEL_PROXY", "Proxy de nivel de servicio basado en disponibilidad mensual", "Derivada", "Numérico", "EDA"],
        ["INVENTORY_TURNOVER_PROXY", "Rotación aproximada del inventario usando ventas mensuales promedio y stock promedio", "Derivada", "Numérico", "EDA"],
    ]

    return pd.DataFrame(rows, columns=[
        "VARIABLE", "DESCRIPCION", "TIPO_VARIABLE", "TIPO_DATO", "FUENTE"
    ])


# -----------------------------
# GRÁFICOS
# -----------------------------
def plot_pareto(ranking: pd.DataFrame):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    x = ranking["RANK"]
    y1 = ranking["TOTAL_SALES"]
    y2 = ranking["CUM_SHARE"] * 100

    ax1.bar(x, y1)
    ax1.set_xlabel("Ranking SKU")
    ax1.set_ylabel("Ventas acumuladas por SKU")
    ax1.set_title("Curva de Pareto de ventas por SKU")

    ax2 = ax1.twinx()
    ax2.plot(x, y2, marker="o")
    ax2.axvline(50, linestyle="--")
    ax2.set_ylabel("% acumulado de ventas")

    plt.tight_layout()
    plt.savefig(EDA_DIR / "pareto_top50_selection.png", dpi=200)
    plt.close()


def plot_top50_specific_skus(top50: pd.DataFrame):
    plot_df = top50.sort_values("TOTAL_SALES", ascending=True).copy()

    plt.figure(figsize=(12, 14))
    plt.barh(plot_df[SKU_COL].astype(str), plot_df["TOTAL_SALES"])
    plt.xlabel("Ventas acumuladas")
    plt.ylabel("SKU")
    plt.title("Top 50 SKU por ventas acumuladas")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "top50_skus_barh.png", dpi=200)
    plt.close()


def plot_abc_xyz_heatmap(abc_xyz: pd.DataFrame):
    pivot = pd.pivot_table(
        abc_xyz,
        index="ABC_CLASS",
        columns="XYZ_CLASS",
        values=SKU_COL,
        aggfunc="count",
        fill_value=0
    ).reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(pivot.values)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("XYZ")
    ax.set_ylabel("ABC")
    ax.set_title("Matriz ABC/XYZ")

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax.text(j, i, str(pivot.iloc[i, j]), ha="center", va="center")

    plt.tight_layout()
    plt.savefig(EDA_DIR / "abc_xyz_matrix.png", dpi=200)
    plt.close()


def plot_abc_sales_concentration(abc_xyz: pd.DataFrame):
    plot_df = (
        abc_xyz.groupby("ABC_CLASS", as_index=False)["TOTAL_SALES"]
        .sum()
        .sort_values("ABC_CLASS")
    )

    plt.figure(figsize=(8, 5))
    plt.bar(plot_df["ABC_CLASS"], plot_df["TOTAL_SALES"])
    plt.xlabel("Clase ABC")
    plt.ylabel("Ventas acumuladas")
    plt.title("Concentración de ventas por clase ABC")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "abc_sales_concentration.png", dpi=200)
    plt.close()


def plot_top10_abc_xyz_combinations(abc_xyz: pd.DataFrame):
    plot_df = (
        abc_xyz["ABC_XYZ"]
        .value_counts()
        .head(10)
        .sort_values(ascending=True)
    )

    plt.figure(figsize=(8, 6))
    plt.barh(plot_df.index.astype(str), plot_df.values)
    plt.xlabel("Número de SKU")
    plt.ylabel("Combinación ABC/XYZ")
    plt.title("Top 10 combinaciones ABC/XYZ más frecuentes")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "top10_abc_xyz_combinations.png", dpi=200)
    plt.close()


def plot_seasonality(df: pd.DataFrame):
    temp = df.copy()
    temp["MONTH_NUM"] = temp[DATE_COL].dt.month

    monthly = temp.groupby("MONTH_NUM", as_index=False)[SALES_COL].mean()

    plt.figure(figsize=(10, 5))
    plt.plot(monthly["MONTH_NUM"], monthly[SALES_COL], marker="o")
    plt.xticks(range(1, 13))
    plt.xlabel("Mes del año")
    plt.ylabel("Venta promedio mensual")
    plt.title("Estacionalidad agregada de la demanda")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "seasonality_overall.png", dpi=200)
    plt.close()


def plot_monthly_total_sales_trend(df: pd.DataFrame):
    monthly = (
        df.groupby(DATE_COL, as_index=False)[SALES_COL]
        .sum()
        .sort_values(DATE_COL)
    )

    plt.figure(figsize=(12, 5))
    plt.plot(monthly[DATE_COL], monthly[SALES_COL], marker="o")
    plt.xticks(rotation=45)
    plt.xlabel("Periodo")
    plt.ylabel("Ventas totales")
    plt.title("Tendencia mensual agregada de ventas")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "monthly_total_sales_trend.png", dpi=200)
    plt.close()


def plot_intermittency(intermittency_df: pd.DataFrame):
    plot_df = intermittency_df.dropna(subset=["ADI", "CV2"]).copy()

    plt.figure(figsize=(10, 6))
    plt.scatter(plot_df["ADI"], plot_df["CV2"])
    plt.axvline(1.32, linestyle="--")
    plt.axhline(0.49, linestyle="--")
    plt.xlabel("ADI")
    plt.ylabel("CV²")
    plt.title("Clasificación de demanda intermitente")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "intermittent_demand_scatter.png", dpi=200)
    plt.close()


def plot_demand_type_distribution(intermittency_df: pd.DataFrame):
    plot_df = intermittency_df["DEMAND_TYPE"].value_counts().sort_values(ascending=False)

    plt.figure(figsize=(8, 5))
    plt.bar(plot_df.index.astype(str), plot_df.values)
    plt.xlabel("Tipo de demanda")
    plt.ylabel("Número de SKU")
    plt.title("Distribución de tipos de demanda")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "demand_type_distribution.png", dpi=200)
    plt.close()


def plot_stockout_top20(baseline_df: pd.DataFrame):
    top = baseline_df.sort_values("STOCKOUT_RATE", ascending=False).head(20)

    plt.figure(figsize=(12, 6))
    plt.bar(top[SKU_COL].astype(str), top["STOCKOUT_RATE"])
    plt.xticks(rotation=90)
    plt.ylabel("Frecuencia de quiebre (proxy)")
    plt.title("Top 20 SKU con mayor frecuencia de quiebre de stock")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "stockout_top20.png", dpi=200)
    plt.close()


def plot_inventory_days_distribution(baseline_df: pd.DataFrame):
    vals = baseline_df["AVG_INVENTORY_DAYS_PROXY"].dropna()

    plt.figure(figsize=(10, 5))
    plt.hist(vals, bins=30)
    plt.xlabel("Días de inventario (proxy)")
    plt.ylabel("Frecuencia")
    plt.title("Distribución de días de inventario")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "inventory_days_distribution.png", dpi=200)
    plt.close()


def plot_stock_coverage_top20(baseline_df: pd.DataFrame):
    plot_df = (
        baseline_df.dropna(subset=["AVG_INVENTORY_DAYS_PROXY"])
        .sort_values("AVG_INVENTORY_DAYS_PROXY", ascending=False)
        .head(20)
        .copy()
    )

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df[SKU_COL].astype(str), plot_df["AVG_INVENTORY_DAYS_PROXY"])
    plt.xticks(rotation=90)
    plt.ylabel("Días de inventario (proxy)")
    plt.title("Top 20 SKU con mayor cobertura de stock")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "stock_coverage_top20.png", dpi=200)
    plt.close()


def plot_inventory_turnover_lowest20(turnover_df: pd.DataFrame):
    plot_df = (
        turnover_df.dropna(subset=["INVENTORY_TURNOVER_PROXY"])
        .sort_values("INVENTORY_TURNOVER_PROXY", ascending=True)
        .head(20)
        .copy()
    )

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df[SKU_COL].astype(str), plot_df["INVENTORY_TURNOVER_PROXY"])
    plt.xticks(rotation=90)
    plt.ylabel("Rotación de inventario (proxy)")
    plt.title("Top 20 SKU con menor rotación de inventario")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "inventory_turnover_top20_lowest.png", dpi=200)
    plt.close()


# -----------------------------
# DIAGNÓSTICO
# -----------------------------
def build_diagnostic_text(
    original_rows,
    deduplicated_rows,
    duplicate_rows_removed,
    full_df,
    ranking,
    top50,
    abc_xyz,
    intermittency_df,
    baseline_df,
    turnover_df,
    critical_vars_df
):
    n_skus = full_df[SKU_COL].nunique()
    start_date = full_df[DATE_COL].min()
    end_date = full_df[DATE_COL].max()

    missing_imputed = int((full_df["record_type"] == "falta_registro_imputada_cero").sum())
    zero_recorded = int((full_df["record_type"] == "demanda_cero_registrada").sum())

    top50_share = top50["TOTAL_SALES"].sum() / ranking["TOTAL_SALES"].sum() if ranking["TOTAL_SALES"].sum() > 0 else 0

    demand_mix = intermittency_df["DEMAND_TYPE"].value_counts(normalize=True).round(4).to_dict()

    avg_stockout = baseline_df["STOCKOUT_RATE"].mean()
    avg_service = baseline_df["SERVICE_LEVEL_PROXY"].mean()
    avg_inventory_days = baseline_df["AVG_INVENTORY_DAYS_PROXY"].dropna().mean()
    avg_turnover = turnover_df["INVENTORY_TURNOVER_PROXY"].dropna().mean()

    text = f"""
# Diagnóstico del proceso actual

## 1. Estructura y granularidad de los datos
- SKUs únicos analizados: {n_skus}
- Periodo histórico disponible: {start_date.date()} a {end_date.date()}
- Granularidad efectiva de la fuente: mensual por SKU
- Observación crítica: la fuente actual no contiene transacciones diarias ni semanales. Por tanto, el EDA se construyó con la mejor granularidad disponible (SKU-mes), y debe documentarse esta limitación para la fase formal del proyecto.

## 2. Calidad de datos
- Registros originales: {original_rows}
- Registros luego de agregación y depuración: {deduplicated_rows}
- Registros duplicados eliminados/agregados: {duplicate_rows_removed}
- Casos de demanda cero registrada: {zero_recorded}
- Casos de falta de registro imputada a cero: {missing_imputed}

Interpretación:
- Se diferenció explícitamente entre 'demanda cero' y 'falta de registro', tal como exige el tutor.
- La depuración consistió en agrupar registros repetidos por SKU-fecha y conservar stock final del periodo.

## 3. Justificación de enfoque en Top 50 SKU
- Los 50 SKU de mayor rotación concentran aproximadamente {top50_share:.2%} de las ventas acumuladas del histórico.
- Esta selección es coherente con el alcance del MVP, que exige una validación piloto sobre productos de mayor relevancia operativa.
- Desde una lógica tipo Pareto, priorizar este subconjunto permite capturar la mayor parte del impacto de negocio en la primera iteración.

## 4. Segmentación de inventario
- Se aplicó clasificación ABC/XYZ para distinguir productos por importancia comercial y previsibilidad.
- Esto permite separar SKU de alta relevancia y alta variabilidad, fundamentales para la toma de decisiones de compra.

## 5. Patrones de demanda
- Mezcla de tipos de demanda observada: {demand_mix}
- El dataset presenta presencia importante de demanda intermitente y/o variable, lo cual es consistente con un entorno de autopartes.
- Este hallazgo justifica que la gestión manual basada solo en intuición o promedio simple pueda generar sobreinventario o quiebres.

## 6. Línea base operativa actual
- Frecuencia promedio proxy de quiebre de stock: {avg_stockout:.2%}
- Nivel de servicio promedio proxy: {avg_service:.2%}
- Días promedio de inventario proxy: {avg_inventory_days:.2f}
- Rotación promedio proxy del inventario: {avg_turnover:.4f}

Interpretación:
- Estas métricas son aproximaciones construidas a nivel mensual, por lo que deben reportarse como línea base proxy, no como indicador operacional exacto diario.

## 7. Variables críticas exigidas por revisión
{critical_vars_df.to_string(index=False)}

Interpretación:
- Si Lead Time o Costos Unitarios no están disponibles en la fuente, debe documentarse como una brecha crítica del proceso actual.
- Esto no invalida el EDA, pero sí limita la precisión futura del sistema de reabastecimiento.

## 8. Diagnóstico general del proceso actual
El proceso actual presenta una base histórica suficiente para modelar demanda por SKU, pero con limitaciones relevantes:
1. La granularidad real de la información es mensual, no diaria ni semanal.
2. No todas las variables logísticas críticas están disponibles en la fuente actual.
3. Existe heterogeneidad fuerte entre productos, tanto en ventas como en variabilidad.
4. La demanda intermitente y la concentración de ventas en pocos SKU justifican el enfoque analítico y el uso posterior de IA.
5. La gestión actual puede estar expuesta a decisiones subóptimas por falta de segmentación, baja trazabilidad de quiebres y ausencia de variables clave como lead time y costo unitario.
"""
    return text.strip()


# -----------------------------
# EXPORTACIÓN
# -----------------------------
def export_all(
    full_df,
    ranking,
    top50,
    abc_xyz,
    intermittency_df,
    baseline_df,
    turnover_df,
    data_dict_df,
    critical_vars_df,
    diagnostic_text
):
    full_df.to_csv(EDA_DIR / "sales_complete_monthly_grid.csv", index=False, encoding="utf-8-sig")
    ranking.to_csv(EDA_DIR / "sku_ranking.csv", index=False, encoding="utf-8-sig")
    top50.to_csv(EDA_DIR / "top50_skus.csv", index=False, encoding="utf-8-sig")
    abc_xyz.to_csv(EDA_DIR / "abc_xyz_classification.csv", index=False, encoding="utf-8-sig")
    intermittency_df.to_csv(EDA_DIR / "intermittency_analysis.csv", index=False, encoding="utf-8-sig")
    baseline_df.to_csv(EDA_DIR / "operational_baseline.csv", index=False, encoding="utf-8-sig")
    turnover_df.to_csv(EDA_DIR / "inventory_turnover_proxy.csv", index=False, encoding="utf-8-sig")
    data_dict_df.to_csv(EDA_DIR / "data_dictionary_minimum.csv", index=False, encoding="utf-8-sig")
    critical_vars_df.to_csv(EDA_DIR / "critical_variables_availability.csv", index=False, encoding="utf-8-sig")

    with open(EDA_DIR / "diagnostic_current_process.md", "w", encoding="utf-8") as f:
        f.write(diagnostic_text)

    excel_path = EDA_DIR / "eda_outputs.xlsx"
    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        ranking.to_excel(writer, sheet_name="SKU_Ranking", index=False)
        top50.to_excel(writer, sheet_name="Top50", index=False)
        abc_xyz.to_excel(writer, sheet_name="ABC_XYZ", index=False)
        intermittency_df.to_excel(writer, sheet_name="Intermitencia", index=False)
        baseline_df.to_excel(writer, sheet_name="Linea_Base", index=False)
        turnover_df.to_excel(writer, sheet_name="Rotacion_Proxy", index=False)
        data_dict_df.to_excel(writer, sheet_name="Diccionario_Datos", index=False)
        critical_vars_df.to_excel(writer, sheet_name="Variables_Criticas", index=False)


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("Cargando datos...")
    sales_df, days_df = load_data()

    print("Depurando duplicados y agregando...")
    monthly_df, original_rows, dedup_rows, dup_removed = aggregate_monthly_sales(sales_df)

    print("Construyendo grilla completa SKU-mes...")
    full_df = build_complete_sku_month_grid(monthly_df)

    print("Calculando ranking y top 50...")
    ranking, top50 = compute_top50(full_df)

    print("Construyendo ABC/XYZ...")
    abc_xyz = build_abc_xyz(full_df)

    print("Analizando demanda intermitente...")
    intermittency_df = compute_intermittency(full_df)

    print("Calculando línea base operativa...")
    baseline_df = compute_operational_baseline(full_df)

    print("Calculando rotación proxy...")
    turnover_df = compute_inventory_turnover_proxy(full_df)

    print("Evaluando disponibilidad de variables críticas...")
    critical_vars_df = assess_critical_variables(days_df)

    print("Generando diccionario de datos...")
    data_dict_df = build_data_dictionary()

    print("Generando gráficos...")
    plot_pareto(ranking)
    plot_top50_specific_skus(top50)
    plot_abc_xyz_heatmap(abc_xyz)
    plot_abc_sales_concentration(abc_xyz)
    plot_top10_abc_xyz_combinations(abc_xyz)
    plot_seasonality(full_df)
    plot_monthly_total_sales_trend(full_df)
    plot_intermittency(intermittency_df)
    plot_demand_type_distribution(intermittency_df)
    plot_stockout_top20(baseline_df)
    plot_inventory_days_distribution(baseline_df)
    plot_stock_coverage_top20(baseline_df)
    plot_inventory_turnover_lowest20(turnover_df)

    print("Construyendo diagnóstico...")
    diagnostic_text = build_diagnostic_text(
        original_rows,
        dedup_rows,
        dup_removed,
        full_df,
        ranking,
        top50,
        abc_xyz,
        intermittency_df,
        baseline_df,
        turnover_df,
        critical_vars_df
    )

    print("Exportando resultados...")
    export_all(
        full_df,
        ranking,
        top50,
        abc_xyz,
        intermittency_df,
        baseline_df,
        turnover_df,
        data_dict_df,
        critical_vars_df,
        diagnostic_text
    )

    print("EDA finalizado.")
    print(f"Resultados en: {EDA_DIR}")


if __name__ == "__main__":
    main()
    