from fastapi_users import schemas
from beanie import Document
from pydantic import Field
from typing import Optional
from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase
from beanie import PydanticObjectId

class User(BeanieBaseUser, Document):
    class Settings:
        collection = "users"  # 指定集合名称

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass

# Remove the UserDB class as it's no longer needed