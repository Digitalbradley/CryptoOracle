"""Authentication API endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate and set JWT cookie."""
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.username)

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    is_production = settings.app_env == "production"

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.jwt_expiry_hours * 3600,
        path="/",
    )

    return {"status": "authenticated", "username": user.username}


@router.post("/logout")
def logout(response: Response):
    """Clear the JWT cookie."""
    response.delete_cookie(key="access_token", path="/")
    return {"status": "logged_out"}


@router.get("/me")
def get_current_user_info(request: Request):
    """Return the currently authenticated user info.

    This endpoint is in the public whitelist so the frontend can check
    auth state on page load. Returns 401 if not authenticated.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": user}
