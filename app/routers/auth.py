from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=settings.algorithm)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 해요")
    if len(body.password) > 72:
        raise HTTPException(status_code=400, detail="비밀번호는 72자 이하여야 해요")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일이에요")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_token(user.id), email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않아요")
    return TokenResponse(access_token=create_token(user.id), email=user.email)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/kakao")
def kakao_login():
    kakao_auth_url = "https://kauth.kakao.com/oauth/authorize"
    params = {
        "client_id": settings.kakao_client_id,
        "redirect_uri": settings.kakao_redirect_uri,
        "response_type": "code"
    }
    return RedirectResponse(url=f"{kakao_auth_url}?{urlencode(params)}")


@router.get("/kakao/callback")
async def kakao_callback(code: str = Query(...), db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.kakao_client_id,
                "client_secret": settings.kakao_client_secret,
                "redirect_uri": settings.kakao_redirect_uri,
                "code": code
            }
        )

        if token_response.status_code != 200:
            error_detail = token_response.text
            print(f"Kakao token error: {token_response.status_code} - {error_detail}")
            raise HTTPException(status_code=400, detail=f"카카오 인증 실패: {error_detail}")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="사용자 정보 조회 실패")

        user_data = user_response.json()
        kakao_id = str(user_data.get("id"))
        email = user_data.get("kakao_account", {}).get("email")

        if not email:
            raise HTTPException(status_code=400, detail="이메일 동의가 필요합니다")

        user = db.query(User).filter(User.provider == "kakao", User.social_id == kakao_id).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.provider = "kakao"
                user.social_id = kakao_id
            else:
                user = User(email=email, provider="kakao", social_id=kakao_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_token(user.id)
        redirect_url = f"https://www.uni-us.site?token={jwt_token}&email={user.email}"
        return RedirectResponse(url=redirect_url)


@router.get("/google")
def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile"
    }
    return RedirectResponse(url=f"{google_auth_url}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "code": code
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="구글 인증 실패")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="사용자 정보 조회 실패")

        user_data = user_response.json()
        google_id = str(user_data.get("id"))
        email = user_data.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="이메일 정보가 필요합니다")

        user = db.query(User).filter(User.provider == "google", User.social_id == google_id).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.provider = "google"
                user.social_id = google_id
            else:
                user = User(email=email, provider="google", social_id=google_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_token(user.id)
        redirect_url = f"https://www.uni-us.site?token={jwt_token}&email={user.email}"
        return RedirectResponse(url=redirect_url)
