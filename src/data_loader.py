import pandas as pd
from src.config import EXCEL_FILE, SALES_SHEET, DAYS_SHEET

def load_excel_data():
    sales_df = pd.read_excel(EXCEL_FILE, sheet_name=SALES_SHEET)
    days_df = pd.read_excel(EXCEL_FILE, sheet_name=DAYS_SHEET)
    return sales_df, days_df
