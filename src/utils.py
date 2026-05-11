import pandas as pd

def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def series_train_test_split(series: pd.Series, test_size: int):
    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    return train, test
