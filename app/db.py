from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_users.db import BeanieUserDatabase
from app.models import User

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["test_db"]

async def get_user_db():
    yield BeanieUserDatabase(User, db["users"])