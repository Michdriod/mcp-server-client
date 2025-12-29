from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db.models import User
import secrets

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Suppress bcrypt version warnings
import warnings
warnings.filterwarnings("ignore", message=".*bcrypt.*version.*", category=UserWarning)

# Password hashing with explicit bcrypt configuration to avoid version warnings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    # Truncate password if it exceeds bcrypt's 72 byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print(f"Warning: Password truncated to 72 bytes for bcrypt compatibility")
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Password hashing error: {e}")
        raise

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

def get_current_user(db: Session, token: str) -> Optional[User]:
    """Get current user from JWT token."""
    payload = verify_token(token)
    if payload is None:
        return None
    
    username = payload.get("sub")
    if username is None:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user

def check_user_permission(user: User, required_role: str) -> bool:
    """Check if user has required role permission."""
    role_hierarchy = {
        "viewer": 1,
        "analyst": 2, 
        "admin": 3
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level