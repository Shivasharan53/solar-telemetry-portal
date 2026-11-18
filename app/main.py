from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pymongo import UpdateOne

from app.database import get_database, mongo_is_enabled, check_connection
from app.demo_data import SAMPLE_INVERTERS, demo_telemetry

app = FastAPI(
    title="SOLARA | Solar Farm Intelligence API",
    description="Multi-vendor solar inverter telemetry, equipment events and fleet analytics.",
    version="1.1.0",
)

def inverter_records():
    db = get_database() if mongo_is_enabled() else None
    if db is not None:
        try:
            records = list(db.inverters.find({}, {"_id": 0}))
            if records:
                return records
        except Exception:
            pass
    return SAMPLE_INVERTERS

@app.get("/")
def root():
    return {"product": "SOLARA", "message": "Solar Farm Intelligence API", "docs": "/docs"}

@app.get("/health")
def health():
    configured = mongo_is_enabled()
    connected = check_connection() if configured else False
    return {
        "status": "ok" if connected or not configured else "degraded",
        "database": "MongoDB connected" if connected else ("demo mode" if not configured else "MongoDB unavailable"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/inverters")
def list_inverters(site: Optional[str] = None, state: Optional[str] = None):
    records = inverter_records()
    if site:
        records = [x for x in records if x.get("site") == site]
    if state:
        records = [x for x in records if x.get("status", {}).get("state") == state]
    return {"count": len(records), "items": records}

@app.get("/api/inverters/{inverter_id}")
def get_inverter(inverter_id: str):
    found = next((x for x in inverter_records() if x.get("inverter_id") == inverter_id), None)
    if found is None:
        raise HTTPException(status_code=404, detail="Inverter not found")
    return found

@app.get("/api/fleet/summary")
def fleet_summary():
    records = inverter_records()
    count = len(records)
    online = sum(x.get("status", {}).get("state") == "online" for x in records)
    return {
        "inverter_count": count,
        "online_count": online,
        "warning_count": sum(x.get("status", {}).get("state") == "warning" for x in records),
        "offline_count": sum(x.get("status", {}).get("state") == "offline" for x in records),
        "current_power_kw": round(sum(x.get("status", {}).get("power_kw", 0) for x in records), 2),
        "snapshot_availability_pct": round(online / count * 100, 2) if count else 0,
    }

@app.get("/api/analytics/availability-by-manufacturer")
def availability_by_manufacturer():
    db = get_database() if mongo_is_enabled() else None
    if db is not None:
        try:
            pipeline = [
                {"$group": {
                    "_id": "$manufacturer",
                    "total_units": {"$sum": 1},
                    "online_units": {"$sum": {"$cond": [{"$eq": ["$status.state", "online"]}, 1, 0]}},
                }},
                {"$project": {
                    "_id": 0,
                    "manufacturer": "$_id",
                    "total_units": 1,
                    "online_units": 1,
                    "snapshot_availability_pct": {
                        "$round": [{"$multiply": [{"$divide": ["$online_units", "$total_units"]}, 100]}, 2]
                    },
                }},
                {"$sort": {"manufacturer": 1}},
            ]
            return list(db.inverters.aggregate(pipeline))
        except Exception:
            pass

    grouped = {}
    for item in SAMPLE_INVERTERS:
        maker = item["manufacturer"]
        grouped.setdefault(maker, {"manufacturer": maker, "total_units": 0, "online_units": 0})
        grouped[maker]["total_units"] += 1
        grouped[maker]["online_units"] += item["status"]["state"] == "online"
    return [
        {**value, "snapshot_availability_pct": round(value["online_units"] / value["total_units"] * 100, 2)}
        for value in sorted(grouped.values(), key=lambda x: x["manufacturer"])
    ]

@app.get("/api/telemetry/{inverter_id}")
def inverter_telemetry(inverter_id: str, limit: int = Query(100, ge=1, le=1000)):
    if not any(x["inverter_id"] == inverter_id for x in inverter_records()):
        raise HTTPException(status_code=404, detail="Inverter not found")
    db = get_database() if mongo_is_enabled() else None
    if db is not None:
        rows = list(db.telemetry.find({"inverter_id": inverter_id}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        if rows:
            return {"inverter_id": inverter_id, "source": "MongoDB", "items": rows}
    rows = demo_telemetry(inverter_id, 24)[-limit:]
    return {"inverter_id": inverter_id, "source": "demo", "items": rows}

@app.post("/api/telemetry/seed")
def seed_demo_data():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Configure MONGODB_URI before seeding.")
    operations = [
        UpdateOne({"inverter_id": item["inverter_id"]}, {"$set": item}, upsert=True)
        for item in SAMPLE_INVERTERS
    ]
    result = db.inverters.bulk_write(operations)
    db.inverters.create_index("inverter_id", unique=True)
    db.inverters.create_index([("manufacturer", 1), ("status.state", 1)])
    db.telemetry.create_index([("inverter_id", 1), ("timestamp", -1)])
    return {
        "message": "Demo inverter documents upserted. Existing unrelated records were not deleted.",
        "matched": result.matched_count,
        "upserted": len(result.upserted_ids),
        "inverter_count": len(SAMPLE_INVERTERS),
    }
