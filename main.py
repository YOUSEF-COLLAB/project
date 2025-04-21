import os
import uvicorn
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from apiiiii.model import predict_label

# ✅ Load environment variables
load_dotenv()

# ✅ Firebase Setup
cred = credentials.Certificate("secrets/firebase-key.json")
  # Make sure this is in .gitignore
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ FastAPI App
app = FastAPI()

# ✅ Sensor Model
class SensorData(BaseModel):
    AccX: float
    AccY: float
    AccZ: float
    GyroX: float
    GyroY: float
    GyroZ: float

# ✅ Predict Driving Behavior from Sensor Data
@app.post("/predict_behavior")
def get_behavior_prediction(sensor: SensorData):
    input_data = [sensor.AccX, sensor.AccY, sensor.AccZ, sensor.GyroX, sensor.GyroY, sensor.GyroZ]
    label = predict_label(input_data)
    if label is None:
        return {"message": "⏳ Waiting for more sensor data to build rolling features."}
    return {"predicted_behavior": label}

# ✅ Vehicle Data Storage (Temporary)
vehicle_data = {}

# ✅ Add Driver to Firestore
@app.post("/add_driver")
def add_driver(name: str, car_type: str, speed: int, rpm: int):
    driver_data = {
        "name": name,
        "car_type": car_type,
        "speed": speed,
        "rpm": rpm
    }
    db.collection("drivers").add(driver_data)
    return {"message": "Driver data saved to Firestore successfully!"}

# ✅ Welcome Message
@app.get("/")
def welcome():
    return {"message": "🚗 Welcome to the Driver Tracking API!"}

# ✅ Fuel Usage Calculation
car_fuel_data = {
    "sedan": 7.5,
    "suv": 10.0,
    "truck": 15.0,
    "electric": 0.0  # Electric cars don’t use fuel
}

@app.get("/fuel-usage")
def fuel_usage(car_type: str, speed: float, hours: float):
    fuel_rate = car_fuel_data.get(car_type.lower())
    if fuel_rate is None:
        return {"error": "Car type not found"}
    fuel_used = (fuel_rate * hours) if speed > 0 else 0
    return {
        "car_type": car_type,
        "speed": speed,
        "hours": hours,
        "fuel_used": fuel_used
    }

# ✅ Speed & RPM Tracking
IDEAL_SPEED = 80
IDEAL_RPM = 90

@app.get("/vehicle")
def track_vehicle(speed: int, rpm: int):
    status = "Running" if speed > 0 else "Stopped"
    warnings = []
    if speed > IDEAL_SPEED:
        warnings.append("⚠️ Speed limit exceeded!")
    if rpm > IDEAL_RPM:
        warnings.append("⚠️ RPM limit exceeded!")
    return {
        "speed": speed,
        "rpm": rpm,
        "status": status,
        "warnings": warnings
    }

# ✅ Set & Get Car Type
@app.post("/set_car")
def set_car(car_type: str, fuel_consumption: float):
    vehicle_data["car_type"] = car_type
    vehicle_data["avg_fuel_consumption"] = fuel_consumption
    return {"message": f"✅ Car type set to {car_type} with avg {fuel_consumption}L/100km"}

@app.get("/get_car")
def get_car():
    return vehicle_data

# ✅ Emergency Alert & Auto Parking
@app.get("/emergency")
def emergency_alert(latitude: float, longitude: float):
    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    return {
        "message": "🚨 Emergency activated! Car parked safely.",
        "location": {"latitude": latitude, "longitude": longitude},
        "google_maps_link": google_maps_link,
        "status": "Parked (Emergency)"
    }

@app.get("/auto-park")
def auto_park(latitude: float, longitude: float, speed: float):
    if speed > 0:
        return {
            "message": "Emergency Parking Activated!",
            "status": "Slowing Down...",
            "current_location": {"latitude": latitude, "longitude": longitude}
        }
    return {"message": "Vehicle is already stopped."}

# ✅ Driver Scoring System
@app.get("/driver-score")
def driver_score(speed: float, rpm: float):
    score = 100
    if rpm < 60:
        score -= 10
    elif rpm > 100:
        score -= 20
    if speed < 50:
        score -= 5
    elif speed > 80 and speed <= 120:
        score -= 15
    elif speed > 120:
        score -= 30
    score = max(0, score)
    if score >= 85:
        rating = "Excellent 🚗🚨"
    elif score >= 65:
        rating = "Good 👍"
    elif score >= 40:
        rating = "Needs Improvement ⚠️"
    else:
        rating = "Dangerous Driving! ❌"
    return {
        "speed": speed,
        "rpm": rpm,
        "score": score,
        "rating": rating
    }

# ✅ Ensure Firebase Port Usage
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)