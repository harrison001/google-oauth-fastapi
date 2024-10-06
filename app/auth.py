from fastapi import Depends, HTTPException
from httpx_oauth.clients.google import GoogleOAuth2
from app.models import User, UserCreate, UserUpdate, UserRead
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY
from app.db import get_user_db
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.manager import BaseUserManager, UserManagerDependency
from fastapi_users.db import BeanieUserDatabase
from beanie import PydanticObjectId
from httpx import AsyncClient
import logging
import secrets
from typing import Any  # 添加这行
from app.oauth_clients import linkedin_oauth_client

class CustomGoogleOAuth2(GoogleOAuth2):
    async def get_id_email(self, token: str):
        async with AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            
            # Add logging here
            logging.debug(f"Raw Google user info: {data}")
            
            return {
                "id": data.get("id"),
                "email": data.get("email"),
            }

# OAuth client configuration
google_oauth_client = CustomGoogleOAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                                   scopes=["openid", "email", "profile"])

# JWT strategy
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

class UserManager(BaseUserManager[User, PydanticObjectId]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    async def create(self, user_create: UserCreate):
        logging.debug(f"Attempting to create user: {user_create}")
        try:
            user_dict = user_create.dict()
            if "password" in user_dict:
                hashed_password = self.password_helper.hash(user_dict["password"])
                user_dict["hashed_password"] = hashed_password
                del user_dict["password"]
            user = await self.user_db.create(user_dict)
            logging.debug(f"User created: {user}")
            return user
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    async def oauth_callback(self, oauth_name: str, access_token: str, account_id: str, account_email: str, expires_at: int | None = None) -> User:
        logging.debug(f"OAuth callback for {oauth_name}: email={account_email}, id={account_id}")
        try:
            user = await self.get_by_email(account_email)
            if user is None:
                # 为 OAuth 用户创建一个随机密码
                random_password = secrets.token_urlsafe(32)
                user = await self.create(
                    UserCreate(email=account_email, password=random_password)
                )
            return user
        except Exception as e:
            logging.error(f"Error in oauth_callback: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process OAuth callback: {str(e)}")

    def parse_id(self, value: Any) -> PydanticObjectId:
        if isinstance(value, PydanticObjectId):
            return value
        try:
            return PydanticObjectId(value)
        except Exception:
            raise ValueError(f"Cannot cast {value} to PydanticObjectId")

async def get_user_manager(user_db: BeanieUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, PydanticObjectId](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

# OAuth routes
def get_oauth_router():
    return fastapi_users.get_oauth_router(
        oauth_client=google_oauth_client,
        backend=auth_backend,
        state_secret=SECRET_KEY,
    )

def get_linkedin_oauth_router():
    return fastapi_users.get_oauth_router(
        oauth_client=linkedin_oauth_client,
        backend=auth_backend,
        state_secret=SECRET_KEY,
    )

def get_oauth_associate_router():
    return fastapi_users.get_oauth_associate_router(
        oauth_client=google_oauth_client,
        user_schema=UserRead,
        state_secret=SECRET_KEY,
    )

def get_linkedin_oauth_associate_router():
    return fastapi_users.get_oauth_associate_router(
        oauth_client=linkedin_oauth_client,
        user_schema=UserRead,
        state_secret=SECRET_KEY,
    )