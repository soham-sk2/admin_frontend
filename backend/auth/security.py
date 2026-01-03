# security.py - Updated version

import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "CHANGE_THIS_TO_A_SECURE_RANDOM_VALUE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash password with SHA-256 first to handle long passwords,
    then bcrypt for security.
    """
    # Hash with SHA-256 first (always 64 characters)
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    # Then bcrypt the SHA-256 hash (always safe for bcrypt)
    return pwd_context.hash(sha256_hash)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password by hashing with SHA-256 first, then checking bcrypt.
    """
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.verify(sha256_hash, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)