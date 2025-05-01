
import os
import uvicorn
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from models.model import predict_label  # Assuming this is your ML model for behavior prediction

# ✅ Load environment variables
load_dotenv()

# ✅ FastAPI App
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Firebase setup
cred = credentials.Certificate("firebase-key.json")  # Make sure this file is in your project root
firebase_admin.initialize_app(cred)
db = firestore.client()
class User(BaseModel):
    email: str
    password: str

# ✅ Signup Route
@app.post("/signup")
async def signup(user: User):
    # Check if user already exists
    existing_user = db.collection("users").where("email", "==", user.email).stream()
    if list(existing_user):
        raise HTTPException(status_code=400, detail="User already exists")

    # Save the new user to Firebase
    db.collection("users").add(user.dict())
    return {"message": "Signup successful!"}

# ✅ Login Route
@app.post("/login")
async def login(user: User):
    # Check if user exists
    existing_user = db.collection("users").where("email", "==", user.email).stream()
    user_data = list(existing_user)

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Check password (this should be hashed in production)
    stored_user = user_data[0].to_dict()
    if stored_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": "Login successful!"}

# ✅ Vehicle Data Storage (Temporary)
vehicle_data = {}

# ✅ API to Add Driver Data
class Driver(BaseModel):
    name: str
    car_type: str
    speed: int
    rpm: int

@app.post("/add_driver")
def add_driver(driver: Driver):
    db.collection("drivers").add(driver.dict())
    return {"message": "Driver data saved to Firebase!"}

# ✅ Behavior Prediction Model
class SensorData(BaseModel):
    AccX: float
    AccY: float
    AccZ: float
    GyroX: float
    GyroY: float
    GyroZ: float

@app.post("/predict_behavior")
def get_behavior_prediction(sensor: SensorData):
    input_data = [sensor.AccX, sensor.AccY, sensor.AccZ, sensor.GyroX, sensor.GyroY, sensor.GyroZ]
    label = predict_label(input_data)
    if label is None:
        return {"message": "⏳ Waiting for more sensor data to build rolling features."}
    return {"predicted_behavior": label}

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
        raise HTTPException(status_code=400, detail="Car type not found")
    
    fuel_used = (fuel_rate * hours) if speed > 0 else 0
    return {
        "car_type": car_type,
        "speed": speed,
        "hours": hours,
        "fuel_used": fuel_used
    }

# ✅ Speed & RPM Tracking
IDEAL_SPEED = 80  # km/h
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
    score = 100  # Start with a perfect score

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

    score = max(0, score)  # Prevent negative scores

    if score >= 85:
        rating = "Excellent 🚗💨"
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

# ✅ Ensure Cloud Run Uses the Correct Port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # ✅ Cloud Run expects this
    uvicorn.run(app, host="0.0.0.0", port=port)
