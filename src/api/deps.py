"""
Shared FastAPI dependencies for authentication.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.db.supabase import supabase

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract and validate the current user from the Supabase JWT
    in the Authorization: Bearer <token> header.

    Returns the full Supabase user dict on success.
    Raises 401 if the token is invalid or expired.
    """
    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)
        return response.user
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
