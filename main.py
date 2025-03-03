from fastapi import FastAPI

app = FastAPI()

# 🚗 Vehicle Data Storage (Example)
car_fuel_data = {
    "sedan": 7.5,
    "suv": 10.0,
    "truck": 15.0,
    "electric": 0.0  # Electric cars don’t use fuel
}

@app.get("/fuel-usage")
def fuel_usage(car_type: str, speed: float, hours: float):
    fuel_rate = car_fuel_data.get(car_type.lower(), None)
    if fuel_rate is None:
        return {"error": "Car type not found"}
    
    fuel_used = (fuel_rate * hours) if speed > 0 else 0
    return {
        "car_type": car_type,
        "speed": speed,
        "hours": hours,
        "fuel_used": fuel_used
    }

# 🚦 Speed & RPM Limits
IDEAL_SPEED = 80  # km/h
IDEAL_RPM = 90

@app.get("/")
def welcome():
    return {"message": "🚗 Welcome to the Driver Tracking API!"}

# 📊 Speed & RPM Endpoint
@app.get("/vehicle")
def track_vehicle(speed: int, rpm: int):
    status = "Running" if speed > 0 else "Stopped"
    
    # 🚨 Warning if exceeding limits
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

# 🚘 Set Car Type & Get Fuel Consumption
@app.post("/set_car")
def set_car(car_type: str, fuel_consumption: float):
    vehicle_data["car_type"] = car_type
    vehicle_data["avg_fuel_consumption"] = fuel_consumption
    return {"message": f"✅ Car type set to {car_type} with avg {fuel_consumption}L/100km"}

@app.get("/get_car")
def get_car():
    return vehicle_data

# 🚨 Emergency Alert & Auto Parking
@app.get("/emergency")
def emergency_alert(latitude: float, longitude: float):
    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    
    return {
        "message": "🚨 Emergency activated! Car parked safely.",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
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

@app.get("/driver-score")
def driver_score(speed: float, rpm: float):
    score = 100  # Start with a perfect score

    # Check RPM 
    if rpm < 60:
        score -= 10  # Penalty for too low RPM (inefficient driving)
    elif rpm > 100:
        score -= 20  # Penalty for too high RPM (aggressive driving)
    
    # Check Speed
    if speed < 50:
        score -= 5  # Slight penalty for too slow (inefficient driving)
    elif speed > 80 and speed <= 120:
        score -= 15  # High speed warning
    elif speed > 120:
        score -= 30  # Dangerous driving!
    
    # Ensure score doesn't go below 0
    score = max(0, score)
    
    # Driver Rating
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
import sqlite3
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./drivers.db"  

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    car_type = Column(String, index=True)
    speed = Column(Integer)
    rpm = Column(Integer)

# ✅ Automatically creates the table if it doesn’t exist
Base.metadata.create_all(bind=engine)