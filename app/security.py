from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

SECURITY_KEY="SUPER_SECRET_RANDOM_STRING"
ALGORITHM="HS256" #HMAC WITH SHA 256"
ACCESS_TOKEN_EXPIRATION_MINUTES=30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECURITY_KEY,algorithm=ALGORITHM)
    return encoded_jwt
    

def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)
