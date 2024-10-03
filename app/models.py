from fastapi_users import schemas
from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional
from fastapi_users.db import BeanieBaseUser
from beanie import PydanticObjectId

class User(BeanieBaseUser, Document):
    email: EmailStr
    hashed_password: str
    
    class Settings:
        name = "users"
        email_collation = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "hashed_password": "string",
                "is_active": True,
                "is_superuser": False,
                "is_verified": False,
            }
        }

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass

# Remove the UserDB class as it's no longer needed