from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_users.db import BeanieUserDatabase
from app.models import User
from app.config import MONGODB_URL, DATABASE_NAME
import logging

async def init_db():
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        await init_beanie(database=client[DATABASE_NAME], document_models=[User])
        logging.info(f"Database '{DATABASE_NAME}' initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise

async def get_user_db():
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        await init_beanie(database=client[DATABASE_NAME], document_models=[User])
        yield BeanieUserDatabase(User)
    except Exception as e:
        logging.error(f"Failed to get user database: {str(e)}")
        raise