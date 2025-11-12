"""
Authentication routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import jwt

from app.models.schemas import LoginRequest, LoginResponse, UserInfo
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint
    
    Demo users:
    - username: admin, password: admin123
    - username: user, password: user123
    """
    username = request.username
    password = request.password
    
    # Check demo users
    user = settings.DEMO_USERS.get(username)
    
    if not user or user['password'] != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token = create_access_token({
        "sub": username,
        "email": user['email']
    })
    
    logger.info(f"User logged in: {username}")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=username,
        email=user['email']
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current user information"""
    return UserInfo(
        username=token_data['sub'],
        email=token_data['email']
    )


@router.post("/logout")
async def logout(token_data: dict = Depends(verify_token)):
    """Logout endpoint (token invalidation handled client-side)"""
    logger.info(f"User logged out: {token_data['sub']}")
    return {"message": "Successfully logged out"}
