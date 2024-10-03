from fastapi import Depends
from httpx_oauth.clients.google import GoogleOAuth2
from app.models import User, UserCreate, UserUpdate, UserRead
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY
from app.db import get_user_db
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.manager import BaseUserManager
from fastapi_users.db import BeanieUserDatabase
from beanie import PydanticObjectId

# OAuth client configuration
google_oauth_client = GoogleOAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)

# JWT strategy
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
jwt_strategy = JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

class UserManager(BaseUserManager[User, PydanticObjectId]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    async def oauth_callback(self, oauth_name: str, access_token: str, account_id: str, account_email: str, expires_at: int | None = None) -> User:
        user = await self.get_by_email(account_email)
        if user is None:
            user = await self.create(
                UserCreate(email=account_email, password=None)
            )
        return user

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

def get_oauth_associate_router():
    return fastapi_users.get_oauth_associate_router(
        oauth_client=google_oauth_client,
        user_schema=UserRead,
        state_secret=SECRET_KEY,
    )