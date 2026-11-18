
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "solar_farm_db")

app = FastAPI(title="Solar Farm Telemetry API", version="1.0.0")
client = AsyncMongoClient(MONGODB_URI) if MONGODB_URI else None
db = client[DATABASE_NAME] if client is not None else None

SAMPLE_INVERTERS = [
    {
        "inverter_id": "INV-001",
        "manufacturer": "SolarEdge",
        "site": "Farm North",
        "status": {"state": "online", "power_kw": 82.5, "temperature_c": 41.2},
        "firmware": {"version": "v2.4.1", "panel_model": "SE-550"},
        "weather": {"condition": "sunny", "irradiance_w_m2": 820},
        "error_logs": [],
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "inverter_id": "INV-002",
        "manufacturer": "SMA",
        "site": "Farm South",
        "status": {"state": "online", "power_kw": 74.2, "temperature_c": 39.8},
        "firmware": {"version": "v3.1.0", "panel_model": "STP-500"},
        "weather": {"condition": "cloudy", "irradiance_w_m2": 610},
        "error_logs": [],
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "inverter_id": "INV-003",
        "manufacturer": "Growatt",
        "site": "Farm East",
        "status": {"state": "warning", "power_kw": 28.4, "temperature_c": 56.1},
        "firmware": {"version": "v1.8.2", "panel_model": "GW-450"},
        "weather": {"condition": "partly cloudy", "irradiance_w_m2": 690},
        "error_logs": [{"code": "TEMP-02", "message": "High inverter temperature"}],
        "updated_at": datetime.now(timezone.utc),
    },
]


@app.get("/")
async def root():
    return {"message": "Solar Farm Telemetry API", "docs": "/docs"}


@app.get("/health")
async def health():
    if db is None:
        return {"status": "configuration_required", "message": "Set MONGODB_URI"}
    try:
        await client.admin.command("ping")
        return {"status": "connected", "database": DATABASE_NAME}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB connection failed: {exc}")


@app.post("/api/telemetry/seed")
async def seed_telemetry():
    if db is None:
        raise HTTPException(status_code=503, detail="Set MONGODB_URI in environment")
    collection = db["inverters"]
    await collection.delete_many({})
    result = await collection.insert_many(SAMPLE_INVERTERS)
    return {"inserted_count": len(result.inserted_ids)}


@app.get("/api/telemetry")
async def get_telemetry():
    if db is None:
        raise HTTPException(status_code=503, detail="Set MONGODB_URI in environment")
    docs = await db["inverters"].find({}, {"_id": 0}).to_list(length=500)
    return docs


@app.get("/api/analytics/uptime-by-manufacturer")
async def uptime_by_manufacturer():
    if db is None:
        raise HTTPException(status_code=503, detail="Set MONGODB_URI in environment")

    pipeline: list[dict[str, Any]] = [
        {
            "$group": {
                "_id": "$manufacturer",
                "total": {"$sum": 1},
                "online": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status.state", "online"]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "manufacturer": "$_id",
                "total": 1,
                "online": 1,
                "uptime_percentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {"$divide": ["$online", "$total"]},
                                100,
                            ]
                        },
                        2,
                    ]
                },
            }
        },
        {"$sort": {"manufacturer": 1}},
    ]

    cursor = await db["inverters"].aggregate(pipeline)
    return await cursor.to_list(length=100)
