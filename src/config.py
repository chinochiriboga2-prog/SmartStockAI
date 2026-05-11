from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

FORECAST_DIR = OUTPUT_DIR / "forecasts"
METRICS_DIR = OUTPUT_DIR / "metrics"
REPORTS_DIR = OUTPUT_DIR / "reports"

EXCEL_FILE = DATA_DIR / "inventory_dataset_sintetico.xlsx"

SALES_SHEET = "INFORME-VENTAS"
DAYS_SHEET = "INFORME-DIAS"

DATE_COL = "FECHA"
SKU_COL = "REFERENCIA"
DESC_COL = "DESCRIPCIÓN"
SALES_COL = "VENTAS"
STOCK_COL = "STOCK"

FORECAST_HORIZON = 3
TOP_N_SKUS = 50
TEST_SIZE = 6

for folder in [OUTPUT_DIR, FORECAST_DIR, METRICS_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
