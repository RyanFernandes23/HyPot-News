"""
Authentication endpoints using Supabase Auth.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.db.supabase import supabase
from src.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response schemas ────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    """Register a new user with email and password."""
    try:
        response = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })

        # Supabase returns user + session; session is None until email is confirmed
        return {
            "message": "Signup successful. Check your email to confirm your account.",
            "user_id": response.user.id,
            "email": response.user.email,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/login")
async def login(body: LoginRequest):
    """Sign in with email and password. Returns access + refresh tokens."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    """Sign out the current user (invalidates the session server-side)."""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully."}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    """Exchange a refresh token for a new access token."""
    try:
        response = supabase.auth.refresh_session(body.refresh_token)

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.get("/me")
async def me(user=Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at),
    }
