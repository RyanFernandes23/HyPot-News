"""
Authentication endpoints using Supabase Auth.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.db.supabase import supabase
from src.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class FCMTokenUpdate(BaseModel):
    fcm_token: str


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
    """Return the profile of the currently authenticated user with auto-sync."""
    try:
        # 1. Fetch from public.users
        profile_res = supabase.table("users").select("*").eq("id", user.id).single().execute()
        profile = profile_res.data or {}

        # 2. Extract metadata from Auth (Google info)
        auth_metadata = getattr(user, "user_metadata", {})
        auth_name = auth_metadata.get("full_name")
        auth_avatar = auth_metadata.get("avatar_url")

        # 3. Auto-sync: if public profile is missing name/avatar, update from OAuth
        updates = {}
        if not profile.get("full_name") and auth_name:
            updates["full_name"] = auth_name
        if not profile.get("avatar_url") and auth_avatar:
            updates["avatar_url"] = auth_avatar
            
        if updates:
            supabase.table("users").update(updates).eq("id", user.id).execute()
            profile.update(updates)

        # 4. Fallback for the first-time return if row doesn't exist yet
        return {
            "id": user.id,
            "email": user.email or profile.get("email"),
            "full_name": profile.get("full_name") or auth_name or "",
            "avatar_url": profile.get("avatar_url") or auth_avatar or "",
            "interests": profile.get("interests") or [],
            "created_at": str(user.created_at),
        }
    except Exception as e:
        # Return at least auth data if public lookup fails
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.user_metadata.get("full_name", ""),
            "avatar_url": user.user_metadata.get("avatar_url", ""),
            "interests": [],
            "created_at": str(user.created_at),
        }


@router.put("/profile")
async def update_profile(body: ProfileUpdate, user=Depends(get_current_user)):
    """Update user's display name and avatar."""
    try:
        updates = {}
        if body.full_name is not None:
            updates["full_name"] = body.full_name
        if body.avatar_url is not None:
            updates["avatar_url"] = body.avatar_url

        if not updates:
            return {"status": "no changes"}

        supabase.table("users").update(updates).eq("id", user.id).execute()
        return {"status": "success", "profile": updates}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {e}",
        )


@router.put("/fcm-token")
async def update_fcm_token(body: FCMTokenUpdate, user=Depends(get_current_user)):
    """Update user's FCM token for push notifications."""
    try:
        supabase.table("users").update({"fcm_token": body.fcm_token}).eq("id", user.id).execute()
        return {"status": "success", "fcm_token": body.fcm_token}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update FCM token: {e}",
        )
