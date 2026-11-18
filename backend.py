import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "solar_farm_db")

app = FastAPI(title="Smart Solar Farm Telemetry API", version="1.0.0")

# Motor Async Client
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
telemetry_col = db["inverter_telemetry"]


class TelemetryPayload(BaseModel):
    inverter_id: str
    manufacturer: str
    plant_zone: str
    status: str  # "ONLINE", "DEGRADED", "FAULT"
    power_output_kw: float
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    firmware_meta: Dict[str, Any] = Field(default_factory=dict)
    vendor_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    weather_context: Dict[str, Any] = Field(default_factory=dict)


@app.on_event("startup")
async def create_indexes():
    await telemetry_col.create_index([("manufacturer", 1), ("timestamp", -1)])
    await telemetry_col.create_index([("inverter_id", 1)])


@app.get("/")
async def root():
    return {"message": "Smart Solar Farm Telemetry API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": DB_NAME}


@app.post("/api/v1/telemetry", status_code=201)
async def ingest_telemetry(payload: TelemetryPayload):
    doc = payload.model_dump()
    result = await telemetry_col.insert_one(doc)
    return {"inserted_id": str(result.inserted_id), "inverter_id": payload.inverter_id}


@app.post("/api/v1/seed")
async def seed_sample_data(count: int = 60):
    """Generates multi-vendor BSON telemetry with heterogeneous schemas."""
    vendors = {
        "SMA Solar": {
            "firmware_meta": {"dsp_ver": "3.14.2", "comm_board": "v2.1", "grid_code": "IEEE-1547"},
            "diagnostics_template": lambda st: {
                "sma_event_code": 0 if st == "ONLINE" else random.choice([3501, 6402, 7701]),
                "iso_resistance_kohm": random.randint(1200, 3500),
                "string_currents_a": [round(random.uniform(8.1, 11.4), 2) for _ in range(4)],
            },
        },
        "Sungrow": {
            "firmware_meta": {"arm_fw": "SG_V11_89", "mppt_algo": "DynamicShade-Pro"},
            "diagnostics_template": lambda st: {
                "alarm_bits": [] if st == "ONLINE" else ["IGBT_OVERTEMP", "DC_ARC_WARN"],
                "internal_temp_c": round(random.uniform(38.0, 68.5), 1),
                "pid_recovery_active": random.choice([True, False]),
            },
        },
        "Huawei FusionSolar": {
            "firmware_meta": {"mbus_version": "V100R001C00SPC152", "optimizer_sync": True},
            "diagnostics_template": lambda st: {
                "smart_iv_curve_status": "PASS" if st == "ONLINE" else "ANOMALY_DETECTED",
                "afci_self_check": "OK",
                "reactive_power_kvar": round(random.uniform(-2.5, 2.5), 2),
            },
        },
        "Enphase": {
            "firmware_meta": {"iq8_image": "520-00082-r01", "envoy_gateway": "D7.6.175"},
            "diagnostics_template": lambda st: {
                "microinverter_grid_profile": "CA Rule 21",
                "plc_signal_strength_db": random.randint(65, 95),
                "ac_frequency_hz": round(random.uniform(59.95, 60.05), 2),
            },
        },
    }

    docs = []
    now = datetime.now(timezone.utc)
    for _ in range(count):
        vendor_name = random.choice(list(vendors.keys()))
        v_cfg = vendors[vendor_name]
        status = random.choices(["ONLINE", "DEGRADED", "FAULT"], weights=[0.82, 0.11, 0.07])[0]
        irradiance = random.randint(250, 1050)
        base_kw = (irradiance / 1000.0) * 50.0
        actual_kw = round(base_kw if status == "ONLINE" else (base_kw * 0.45 if status == "DEGRADED" else 0.0), 2)

        weather = {"irradiance_wm2": irradiance, "ambient_temp_c": round(random.uniform(22, 41), 1)}
        if random.random() > 0.4:
            weather["wind_speed_mps"] = round(random.uniform(1.2, 9.8), 1)
        if random.random() > 0.6:
            weather["soiling_loss_pct"] = round(random.uniform(0.5, 4.2), 2)

        docs.append({
            "inverter_id": f"INV-{vendor_name[:3].upper()}-{random.randint(101, 115)}",
            "manufacturer": vendor_name,
            "plant_zone": random.choice(["North-Array-A", "South-Array-B", "East-Tracker-C"]),
            "status": status,
            "power_output_kw": actual_kw,
            "timestamp": now - timedelta(minutes=random.randint(0, 720)),
            "firmware_meta": v_cfg["firmware_meta"],
            "vendor_diagnostics": v_cfg["diagnostics_template"](status),
            "weather_context": weather,
        })

    await telemetry_col.insert_many(docs)
    return {"seeded_records": len(docs)}


@app.get("/api/v1/analytics/uptime-by-manufacturer")
async def get_uptime_by_manufacturer():
    """MongoDB Aggregation Pipeline computing uptime percentages by manufacturer."""
    pipeline = [
        {
            "$group": {
                "_id": "$manufacturer",
                "total_pings": {"$sum": 1},
                "online_pings": {"$sum": {"$cond": [{"$eq": ["$status", "ONLINE"]}, 1, 0]}},
                "degraded_pings": {"$sum": {"$cond": [{"$eq": ["$status", "DEGRADED"]}, 1, 0]}},
                "fault_pings": {"$sum": {"$cond": [{"$eq": ["$status", "FAULT"]}, 1, 0]}},
                "avg_power_kw": {"$avg": "$power_output_kw"},
                "active_inverters": {"$addToSet": "$inverter_id"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "manufacturer": "$_id",
                "inverter_count": {"$size": "$active_inverters"},
                "total_pings": 1,
                "online_pings": 1,
                "degraded_pings": 1,
                "fault_pings": 1,
                "uptime_percentage": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$online_pings", "$total_pings"]}, 100]},
                        2,
                    ]
                },
                "avg_power_kw": {"$round": ["$avg_power_kw", 2]},
            }
        },
        {"$sort": {"uptime_percentage": -1}},
    ]
    return await telemetry_col.aggregate(pipeline).to_list(length=100)


@app.get("/api/v1/telemetry/recent")
async def get_recent_telemetry(manufacturer: Optional[str] = None, limit: int = 25):
    query = {}
    if manufacturer and manufacturer != "All":
        query["manufacturer"] = manufacturer
    cursor = telemetry_col.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)
