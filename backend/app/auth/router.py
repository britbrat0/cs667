from fastapi import APIRouter

from app.models import UserRegister, UserLogin, TokenResponse
from app.auth.service import register_user, login_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(user: UserRegister):
    token = register_user(user.email, user.password)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    token = login_user(user.email, user.password)
    return TokenResponse(access_token=token)
