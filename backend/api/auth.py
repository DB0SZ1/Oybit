"""
Oybit — JWT Authentication
Single-user auth for Ahmad. No registration. No multi-user.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.config import SECRET_KEY
from backend.logger import get_logger

logger = get_logger("auth")

router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Config ────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72  # 3 days — Ahmad's personal tool, not a bank

# Single user — hardcoded credentials
# In production, hash the password. For single-user personal tool, this is fine.
AHMAD_USERNAME = "ahmad"
AHMAD_PASSWORD_HASH = "oybit2026"  # Ahmad changes this in .env or here

security = HTTPBearer(auto_error=False)


# ── Schemas ───────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class UserInfo(BaseModel):
    username: str
    role: str = "admin"


# ── Token Helpers ─────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


# ── Dependency — use on all protected routes ──────────
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserInfo:
    """FastAPI dependency: validates JWT and returns current user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(credentials.credentials)
    return UserInfo(username=payload.get("sub", "ahmad"))


# ── Endpoints ─────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticate Ahmad and return JWT."""
    if req.username != AHMAD_USERNAME or req.password != AHMAD_PASSWORD_HASH:
        logger.warning("Failed login attempt", extra={"username": req.username})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    token = create_access_token(data={"sub": req.username}, expires_delta=expires)
    expires_at = (datetime.utcnow() + expires).isoformat() + "Z"

    logger.info("Login successful", extra={"username": req.username})
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.get("/me", response_model=UserInfo)
def get_me(user: UserInfo = Depends(get_current_user)):
    """Return current authenticated user."""
    return user
