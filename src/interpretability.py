from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

import shap
from lime.lime_tabular import LimeTabularExplainer

from src.config import (
    EXCEL_FILE,
    SALES_SHEET,
    DATE_COL,
    SKU_COL,
    DESC_COL,
    SALES_COL,
    STOCK_COL,
    REPORTS_DIR,
)
from src.preprocessing import clean_sales_data


INTERP_DIR = REPORTS_DIR / "interpretability"
INTERP_DIR.mkdir(parents=True, exist_ok=True)


def safe_rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def safe_mape(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def load_sales():
    df = pd.read_excel(EXCEL_FILE, sheet_name=SALES_SHEET)
    df = clean_sales_data(df)
    return df


def classify_abc_from_full_history(df: pd.DataFrame) -> pd.DataFrame:
    abc = (
        df.groupby(SKU_COL, as_index=False)[SALES_COL]
        .sum()
        .rename(columns={SALES_COL: "TOTAL_SALES"})
        .sort_values("TOTAL_SALES", ascending=False)
    )
    total = abc["TOTAL_SALES"].sum()
    abc["CUM_SHARE"] = abc["TOTAL_SALES"].cumsum() / total if total > 0 else 0

    def f(x):
        if x <= 0.80:
            return "A"
        if x <= 0.95:
            return "B"
        return "C"

    abc["ABC_CLASS"] = abc["CUM_SHARE"].apply(f)
    return abc[[SKU_COL, "ABC_CLASS"]]


def classify_xyz_from_full_history(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for sku, g in df.groupby(SKU_COL):
        s = g.sort_values(DATE_COL)[SALES_COL].astype(float)
        mean_ = s.mean()
        std_ = s.std(ddof=0)

        if mean_ == 0:
            cv = np.inf if std_ > 0 else 0
        else:
            cv = std_ / mean_

        if cv <= 0.5:
            xyz = "X"
        elif cv <= 1.0:
            xyz = "Y"
        else:
            xyz = "Z"

        records.append({
            SKU_COL: sku,
            "XYZ_CLASS": xyz,
            "CV_FULL": None if not np.isfinite(cv) else float(cv)
        })

    return pd.DataFrame(records)


def build_supervised_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values([SKU_COL, DATE_COL])

    abc = classify_abc_from_full_history(df)
    xyz = classify_xyz_from_full_history(df)

    frames = []

    for sku, g in df.groupby(SKU_COL):
        g = g.sort_values(DATE_COL).copy()

        g["lag_1"] = g[SALES_COL].shift(1)
        g["lag_2"] = g[SALES_COL].shift(2)
        g["lag_3"] = g[SALES_COL].shift(3)

        g["roll_mean_3"] = g[SALES_COL].shift(1).rolling(3).mean()
        g["roll_mean_6"] = g[SALES_COL].shift(1).rolling(6).mean()

        g["roll_std_3"] = g[SALES_COL].shift(1).rolling(3).std()
        g["roll_std_6"] = g[SALES_COL].shift(1).rolling(6).std()

        g["nonzero_last_6"] = (
            g[SALES_COL].shift(1).rolling(6).apply(lambda x: np.sum(np.array(x) > 0), raw=True)
        )

        g["month"] = g[DATE_COL].dt.month
        g["year"] = g[DATE_COL].dt.year

        g["target_next_month"] = g[SALES_COL].shift(-1)

        frames.append(g)

    data = pd.concat(frames, ignore_index=True)

    data = data.merge(abc, on=SKU_COL, how="left")
    data = data.merge(xyz, on=SKU_COL, how="left")

    data["ABC_CLASS"] = data["ABC_CLASS"].map({"A": 3, "B": 2, "C": 1})
    data["XYZ_CLASS"] = data["XYZ_CLASS"].map({"X": 1, "Y": 2, "Z": 3})

    data[STOCK_COL] = pd.to_numeric(data[STOCK_COL], errors="coerce").fillna(0)

    feature_cols = [
        "lag_1",
        "lag_2",
        "lag_3",
        "roll_mean_3",
        "roll_mean_6",
        "roll_std_3",
        "roll_std_6",
        "nonzero_last_6",
        STOCK_COL,
        "month",
        "year",
        "ABC_CLASS",
        "XYZ_CLASS",
        "CV_FULL",
    ]

    dataset = data[[SKU_COL, DESC_COL, DATE_COL] + feature_cols + ["target_next_month"]].copy()
    dataset = dataset.dropna().reset_index(drop=True)

    return dataset


def train_surrogate_model(dataset: pd.DataFrame):
    feature_cols = [
        "lag_1",
        "lag_2",
        "lag_3",
        "roll_mean_3",
        "roll_mean_6",
        "roll_std_3",
        "roll_std_6",
        "nonzero_last_6",
        STOCK_COL,
        "month",
        "year",
        "ABC_CLASS",
        "XYZ_CLASS",
        "CV_FULL",
    ]

    dataset = dataset.sort_values(DATE_COL).reset_index(drop=True)

    split_idx = int(len(dataset) * 0.8)
    train_df = dataset.iloc[:split_idx].copy()
    test_df = dataset.iloc[split_idx:].copy()

    X_train = train_df[feature_cols]
    y_train = train_df["target_next_month"]

    X_test = test_df[feature_cols]
    y_test = test_df["target_next_month"]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)

    metrics = {
        "MAE": mean_absolute_error(y_test, pred),
        "RMSE": safe_rmse(y_test, pred),
        "MAPE": safe_mape(y_test, pred),
        "N_TRAIN": len(train_df),
        "N_TEST": len(test_df),
    }

    return model, X_train, X_test, y_train, y_test, pred, metrics, feature_cols, test_df


def generate_shap_outputs(model, X_train, X_test, feature_cols):
    sample_test = X_test.sample(min(200, len(X_test)), random_state=42)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample_test)

    # summary bar
    plt.figure()
    shap.summary_plot(shap_values, sample_test, feature_names=feature_cols, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(INTERP_DIR / "shap_summary_bar.png", dpi=200, bbox_inches="tight")
    plt.close()

    # summary beeswarm
    plt.figure()
    shap.summary_plot(shap_values, sample_test, feature_names=feature_cols, show=False)
    plt.tight_layout()
    plt.savefig(INTERP_DIR / "shap_summary_beeswarm.png", dpi=200, bbox_inches="tight")
    plt.close()

    importance = pd.DataFrame({
        "feature": feature_cols,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0)
    }).sort_values("mean_abs_shap", ascending=False)

    importance.to_csv(INTERP_DIR / "shap_feature_importance.csv", index=False, encoding="utf-8-sig")

    return explainer, shap_values, sample_test, importance


def generate_local_shap_plot(explainer, X_test, feature_cols):
    sample_idx = min(5, len(X_test) - 1)
    row = X_test.iloc[[sample_idx]]
    shap_row = explainer.shap_values(row)

    plt.figure()
    shap.plots._waterfall.waterfall_legacy(
        explainer.expected_value,
        shap_row[0],
        feature_names=feature_cols,
        features=row.iloc[0],
        show=False
    )
    plt.tight_layout()
    plt.savefig(INTERP_DIR / "shap_local_waterfall.png", dpi=200, bbox_inches="tight")
    plt.close()

    return sample_idx


def generate_lime_output(model, X_train, X_test, feature_cols):
    explainer = LimeTabularExplainer(
        training_data=X_train.values,
        feature_names=feature_cols,
        mode="regression",
        discretize_continuous=True,
        random_state=42
    )

    idx = min(5, len(X_test) - 1)
    exp = explainer.explain_instance(
        X_test.iloc[idx].values,
        model.predict,
        num_features=8
    )

    with open(INTERP_DIR / "lime_local_explanation.html", "w", encoding="utf-8") as f:
        f.write(exp.as_html())

    lime_df = pd.DataFrame(exp.as_list(), columns=["feature_condition", "weight"])
    lime_df.to_csv(INTERP_DIR / "lime_local_explanation.csv", index=False, encoding="utf-8-sig")

    return idx


def export_metrics(metrics: dict):
    pd.DataFrame([metrics]).to_csv(
        INTERP_DIR / "surrogate_metrics.csv",
        index=False,
        encoding="utf-8-sig"
    )


def main():
    print("Cargando datos...")
    sales_df = load_sales()

    print("Construyendo dataset supervisado para interpretabilidad...")
    dataset = build_supervised_dataset(sales_df)
    dataset.to_csv(INTERP_DIR / "interpretability_dataset.csv", index=False, encoding="utf-8-sig")

    print("Entrenando modelo sustituto...")
    model, X_train, X_test, y_train, y_test, pred, metrics, feature_cols, test_df = train_surrogate_model(dataset)
    export_metrics(metrics)

    print("Generando SHAP global...")
    explainer, shap_values, sample_test, importance = generate_shap_outputs(model, X_train, X_test, feature_cols)

    print("Generando SHAP local...")
    shap_idx = generate_local_shap_plot(explainer, X_test, feature_cols)

    print("Generando LIME local...")
    lime_idx = generate_lime_output(model, X_train, X_test, feature_cols)

    # export cases
    local_cases = pd.DataFrame({
        "type": ["shap_case", "lime_case"],
        "index_in_test": [shap_idx, lime_idx]
    })
    local_cases.to_csv(INTERP_DIR / "local_cases_index.csv", index=False, encoding="utf-8-sig")

    print("Listo.")
    print(f"Archivos generados en: {INTERP_DIR}")


if __name__ == "__main__":
    main()
    