from fastapi import FastAPI, Depends
from app.auth import fastapi_users, current_active_user, get_oauth_router, get_oauth_associate_router, auth_backend
from app.models import User, UserCreate, UserRead, UserUpdate

app = FastAPI()

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

# Include OAuth routers
app.include_router(get_oauth_router(), prefix="/auth/google", tags=["auth"])
app.include_router(get_oauth_associate_router(), prefix="/auth/associate/google", tags=["auth"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Google OAuth example!"}

@app.get("/protected-route")
async def protected_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello, {user.email}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)