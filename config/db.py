from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI not set in .env file")

client = AsyncIOMotorClient(MONGO_URI, server_api=ServerApi("1"))
db = client["transcription_service"]

def connect():
    return db