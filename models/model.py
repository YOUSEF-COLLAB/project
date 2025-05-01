# apiiiii/model.py

import pandas as pd
import numpy as np
import joblib
from collections import deque  # To store past readings for rolling calculations

# Load the trained model
rf_model = r"C:\Users\HP\apiiiii\models\random2_forest_model.pkl"  # Update the path to match your structure

# Store the last N readings for rolling calculations
window_size = 60  # Use the same window size as training
sensor_history = deque(maxlen=window_size)

# Function to compute features for a new reading
def compute_motion_features_from_new_reading(new_reading):
    global sensor_history

    # Append new reading to history
    sensor_history.append(new_reading)

    # Convert to DataFrame for processing
    df = pd.DataFrame(sensor_history, columns=["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

    # Compute jerk (change in acceleration)
    for col in ["AccX", "AccY", "AccZ"]:
        df[f"{col}_jerk"] = df[col].diff()

    # Compute rolling mean & standard deviation
    for col in ["AccX", "AccY", "AccZ"]:
        df[f"{col}_rolling_mean"] = df[col].rolling(window=window_size, min_periods=1).mean()
        df[f"{col}_rolling_std"] = df[col].rolling(window=window_size, min_periods=1).std()

    # Take the most recent row (latest reading with computed features)
    latest_features = df.iloc[-1:]

    # Drop the original sensor readings before inputting into the model
    drop_columns = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]
    latest_features = latest_features.drop(columns=drop_columns, errors='ignore')

    return latest_features

# Function to predict label for a single reading
def predict_label(new_reading):
    processed_features = compute_motion_features_from_new_reading(new_reading)

    # Handle cases where not enough data for computation
    if processed_features.isnull().values.any():
        print("Not enough data yet to compute features. Keep sending readings.")
        return None

    # Predict label using the trained model
    prediction = rf_model.predict(processed_features)
    return prediction[0]  # Return the label