from fastapi import FastAPI, Depends, APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from .auth import fastapi_users, current_active_user, google_oauth_client, get_user_manager, UserManager, auth_backend, get_linkedin_oauth_router, get_linkedin_oauth_associate_router
from .models import User, UserCreate, UserRead, UserUpdate
from .config import SECRET_KEY, MONGODB_URL, DATABASE_NAME
from .db import init_db
from .oauth_clients import linkedin_oauth_client
from app.oauth_clients import linkedin_oauth_client

import logging
import secrets
import httpx
import json

# 修改日志级别，去掉心跳日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URL, DATABASE_NAME

@app.on_event("startup")
async def startup_event():
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        await client.server_info()  # 这将触发一个到数据库的连接
        logging.info(f"Successfully connected to MongoDB at {MONGODB_URL}")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    await init_db()

# Include FastAPI Users routers
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# 接在 include_router 中调用 get_oauth_router()
# app.include_router(get_oauth_router(), prefix="/auth/google", tags=["auth"])
# app.include_router(get_oauth_associate_router(), prefix="/auth/associate/google", tags=["auth"])

oauth_router = APIRouter()

@oauth_router.get("/login")
async def google_oauth_login():
    try:
        state = secrets.token_urlsafe(16)
        authorization_url = await google_oauth_client.get_authorization_url(
            "http://localhost:8000/auth/google/callback",
            state=state
        )
        return RedirectResponse(url=authorization_url)
    except Exception as e:
        logger.error(f"Error in google_oauth_login: {str(e)}")
        return {"error": str(e)}

@oauth_router.get("/callback")
async def google_oauth_callback(request: Request, user_manager: UserManager = Depends(get_user_manager)):
    try:
        # Get the authorization code from the query parameters
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Exchange the code for an access token
        token = await google_oauth_client.get_access_token(code, request.url_for("google_oauth_callback"))
        logging.debug(f"Received token: {token}")

        # Get user info using the access token
        user_data = await google_oauth_client.get_id_email(token["access_token"])
        logging.info(f"Received Google user data: {user_data}")

        email = user_data["email"]
        first_name = user_data.get("given_name")
        last_name = user_data.get("family_name")
        picture = user_data.get("picture")

        # Check if user exists, if not, create a new user
        try:
            user = await user_manager.get_by_email(email)
            logging.info(f"Existing user found: {user}")
        except Exception as e:
            logging.error(f"Error getting user by email: {str(e)}")
            user = None

        if user is None:
            try:
                user = await user_manager.create(
                    UserCreate(
                        email=email,
                        password=secrets.token_urlsafe(32),
                        first_name=first_name,
                        last_name=last_name,
                        picture=picture,
                        oauth_provider="google"
                    )
                )
                logging.info(f"New user created: {user}")
            except Exception as e:
                logging.error(f"Error creating new user: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to create new user")
        else:
            # 更新现有用户的信息
            user.first_name = first_name
            user.last_name = last_name
            user.picture = picture
            user.oauth_provider = "google"
            await user.save()
            logging.info(f"User updated: {user}")

        # Create access token
        try:
            access_token = await auth_backend.get_strategy().write_token(user)
            logging.debug(f"Access token created: {access_token}")
        except Exception as e:
            logging.error(f"Error creating access token: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create access token")

        # Redirect to success page with access token
        return RedirectResponse(url=f"/auth-success?access_token={access_token}")

    except ValueError as ve:
        logging.error(f"ValueError in google_oauth_callback: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Error in google_oauth_callback: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to process Google OAuth callback: {str(e)}")

# 确保这行在定义了所有 oauth_router 路由之后
app.include_router(oauth_router, prefix="/auth/google", tags=["auth"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Google OAuth example!"}

@app.get("/protected-route")
async def protected_route(user: User = Depends(current_active_user)):
    oauth_provider = user.oauth_provider or "Email"
    
    # 打印获取到的用户信息
    logger.info(f"User info: {user.dict()}")
    
    return {
        "message": f"Hello, {user.first_name or ''} {user.last_name or ''}!",
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "picture": user.picture,
        "oauth_provider": oauth_provider,
        "additional_info": f"You logged in using {oauth_provider} authentication."
    }

@app.get("/test")
async def test_route():
    return {"message": "Test route is working"}

@app.get("/test-oauth-client")
async def test_oauth_client():
    state = secrets.token_urlsafe(16)
    authorization_url = await google_oauth_client.get_authorization_url(
        "http://localhost:8000/auth/google/callback",
        state=state
    )
    return {"authorization_url": authorization_url}

@app.get("/auth-success", response_class=HTMLResponse)
async def auth_success(access_token: str):
    return f"""
    <html>
        <head>
            <title>Authentication Successful</title>
        </head>
        <body>
            <h1>Authentication Successful</h1>
            <p>Your access token is: {access_token}</p>
            <script>
                // 这里可以添加将令牌存储到localStorage的代码
                localStorage.setItem('access_token', '{access_token}');
            </script>
        </body>
    </html>
    """

# LinkedIn OAuth routes
linkedin_oauth_router = APIRouter()

@linkedin_oauth_router.get("/login")
async def linkedin_login():
    redirect_uri = "http://localhost:8000/auth/linkedin/callback"
    state = secrets.token_urlsafe(16)
    authorization_url = await linkedin_oauth_client.get_authorization_url(redirect_uri, state)
    return RedirectResponse(url=authorization_url)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, user_manager: UserManager = Depends(get_user_manager)):
    try:
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        redirect_uri = "http://localhost:8000/auth/linkedin/callback"
        token = await linkedin_oauth_client.get_access_token(code, redirect_uri)
        logging.debug(f"Received LinkedIn token: {token}")

        # 使用 OpenID Connect 的 userinfo 端点获取用户信息
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
            response.raise_for_status()
            user_data = response.json()
            logging.info(f"Received LinkedIn user data: {user_data}")

        email = user_data.get("email")
        first_name = user_data.get("given_name")
        last_name = user_data.get("family_name")
        picture = user_data.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in user data")

        # 检查用户是否存在，如果不存在则创建新用户
        try:
            user = await user_manager.get_by_email(email)
        except Exception:
            user = None

        if user is None:
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=secrets.token_urlsafe(32),
                    first_name=first_name,
                    last_name=last_name,
                    picture=picture,
                    oauth_provider="linkedin"
                )
            )
            logging.info(f"New user created: {user.dict()}")
        else:
            # 更新现有用户的信息
            user.first_name = first_name
            user.last_name = last_name
            user.picture = picture
            user.oauth_provider = "linkedin"
            await user.save()
            logging.info(f"User updated: {user.dict()}")

        # 创建访问令牌
        access_token = await auth_backend.get_strategy().write_token(user)
        logging.debug(f"Access token created: {access_token}")

        # 重定向到成功页面，带上访问令牌
        return RedirectResponse(url=f"/auth-success?access_token={access_token}")

    except Exception as e:
        logging.error(f"Error in LinkedIn callback: {str(e)}")
        return RedirectResponse(url=f"/auth-error?error=unexpected_error&description={str(e)}")

# 添加 LinkedIn OAuth 路由
app.include_router(linkedin_oauth_router, prefix="/auth/linkedin", tags=["auth"])

# 修改测试路由
@app.get("/test-linkedin-oauth-client")
async def test_linkedin_oauth_client():
    state = secrets.token_urlsafe(16)
    authorization_url = await linkedin_oauth_client.get_authorization_url(
        "http://localhost:8000/auth/linkedin/callback",
        state=state
    )
    return {"authorization_url": authorization_url}

@app.get("/auth-error")
async def auth_error(error: str, description: str):
    return {"message": "Authentication failed", "error": error, "description": description}

@app.get("/auth-success")
async def auth_success(access_token: str):
    return {"message": "Authentication successful", "access_token": access_token}

if __name__ == "__main__":
    import uvicorn
    
    print("Registered routes:")
    for route in app.routes:
        print(f"Path: {route.path}")
        print(f"Name: {route.name}")
        print(f"Methods: {route.methods}")
        print("---")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")

# 在所有 app.include_router() 调用之后添加
for route in app.routes:
    logger.debug(f"Registered route: {route.path}")