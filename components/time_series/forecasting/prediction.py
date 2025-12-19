import asyncio
import pickle
from importlib.resources import files

import numpy as np
from tensorflow.keras.models import load_model
from time_series.forecasting.weather import get_todays_temp

TIMESTEPS = 48


def load_model_and_scalers():
    base = files("time_series.forecasting.assets")

    model_path = base / "lstm_energy_weather_model.keras"
    scaler_path = base / "scalers.pkl"

    model = load_model(model_path)

    with scaler_path.open("rb") as f:
        scalers = pickle.load(f)

    return model, scalers


def scale_last(last, scalers):
    last_scaled = last.copy()
    last_scaled[:, 0] = scalers["energy(kWh/hh)"].transform(last_scaled[:, 0].reshape(-1, 1)).flatten()
    last_scaled[:, 1] = scalers["temperature"].transform(last_scaled[:, 1].reshape(-1, 1)).flatten()

    return last_scaled


def recursive_predict(
    last_scaled,
    model,
    scalers,
    future_steps=12,
    numeric_cols=["energy(kWh/hh)", "temperature"],
):
    predictions_scaled = []
    input_window = last_scaled.copy()

    for step in range(future_steps):
        X = input_window.reshape(1, TIMESTEPS, len(numeric_cols))
        pred_scaled = model.predict(X)[0]  # shape (2,)
        predictions_scaled.append(pred_scaled)
        input_window = np.vstack([input_window[1:], pred_scaled])
    predictions_scaled = np.array(predictions_scaled)
    pred_energy_real = scalers["energy(kWh/hh)"].inverse_transform(predictions_scaled[:, 0].reshape(-1, 1)).flatten()
    pred_temp_real = scalers["temperature"].inverse_transform(predictions_scaled[:, 1].reshape(-1, 1)).flatten()

    return pred_energy_real, pred_temp_real


def predict(user_data: list, city: str) -> list:
    if len(user_data) < TIMESTEPS:
        raise ValueError(f"Invalid user_data length: {len(user_data)}. Expected {TIMESTEPS}.")
    data = np.asarray(user_data)
    # based on values from https://weatherspark.com/y/45062/Average-Weather-in-London-United-Kingdom-Year-Round
    avg_temp = 12  # (6 + 6 + 8 + 11 + 14 + 17 + 19 + 19 + 16 + 13 + 9 + 7) / 12
    temp = asyncio.run(get_todays_temp(city))
    if temp is not None:
        data = np.c_[data, np.full(len(user_data), temp)]
    else:
        data = np.c_[data, np.full(len(user_data), avg_temp)]
    model, scalers = load_model_and_scalers()
    last_raw = data[0:48]
    last_scaled = scale_last(last_raw, scalers)
    energy_pred_12, temp_pred_12 = recursive_predict(last_scaled, model, scalers)
    return energy_pred_12.tolist()
