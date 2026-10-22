from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from datetime import datetime, timedelta, timezone
from jose import jwt

SECURITY_KEY="SUPER_SECRET_RANDOM_STRING"
ALGORITHM="HS256" #HMAC WITH SHA 256"
ACCESS_TOKEN_EXPIRATION_MINUTES=30

pwd_context = PasswordHash((Argon2Hasher(), BcryptHasher()))

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
    # bcrypt 5 rejects inputs longer than 72 bytes for legacy bcrypt hashes.
    if BcryptHasher.identify(hashed_password) and len(plain_password.encode("utf-8")) > 72:
        return False
    return pwd_context.verify(plain_password, hashed_password)
