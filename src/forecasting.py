import numpy as np
import pandas as pd
from pmdarima import auto_arima

def forecast_naive_last(train: pd.Series, horizon: int):
    last_value = train.iloc[-1] if len(train) > 0 else 0
    forecast = np.repeat(last_value, horizon)
    return forecast, "naive_last"

def forecast_moving_average(train: pd.Series, horizon: int, window: int = 3):
    if len(train) == 0:
        return np.repeat(0, horizon), "moving_average"

    effective_window = min(window, len(train))
    avg_value = train.tail(effective_window).mean()
    forecast = np.repeat(avg_value, horizon)
    return forecast, "moving_average"

def forecast_auto_arima(train: pd.Series, horizon: int):
    model = auto_arima(
        train,
        seasonal=False,
        suppress_warnings=True,
        error_action="ignore",
        stepwise=True,
        max_p=3,
        max_q=3,
        max_d=2
    )
    forecast = model.predict(n_periods=horizon)
    forecast = np.maximum(forecast, 0)
    return forecast, "auto_arima"

def choose_and_forecast(train: pd.Series, horizon: int):
    train = train.astype(float)

    non_zero_count = (train > 0).sum()
    unique_values = train.nunique()

    if len(train) < 6 or unique_values <= 1:
        return forecast_naive_last(train, horizon)

    if non_zero_count < 6:
        return forecast_moving_average(train, horizon, window=3)

    try:
        return forecast_auto_arima(train, horizon)
    except Exception:
        try:
            return forecast_moving_average(train, horizon, window=3)
        except Exception:
            return forecast_naive_last(train, horizon)
