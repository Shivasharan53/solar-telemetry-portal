import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

@lru_cache(maxsize=1)
def get_client():
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        return None
    return MongoClient(uri, serverSelectionTimeoutMS=5000)

def get_database():
    client = get_client()
    if client is None:
        return None
    return client[os.getenv("DATABASE_NAME", "solar_farm_db")]

def mongo_is_enabled():
    return os.getenv("USE_MONGODB", "true").lower() == "true" and bool(os.getenv("MONGODB_URI", "").strip())

def check_connection():
    client = get_client()
    if client is None:
        return False
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False
