from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.models.user import User

from app import security
from app.crud import users as crud
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.session import get_db
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import timedelta


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")


@router.post("", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_email(db, email=user.email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )
    try:
        return crud.create_user(db, user=user)
    except crud.DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[UserResponse])
def get_all_user(db: Session = Depends(get_db)):
    return crud.get_user_all(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_specific_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    if crud.get_user(db, user_id=user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    existing = crud.get_user_email(db, email=user.email)
    if existing is not None and existing.id != user_id:
        raise HTTPException(status_code=409, detail="Email already exists")
    try:
        return crud.user_update(db, user_id=user_id, user_data=user)
    except crud.DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return db_user

@router.post("/token")
def login_for_access_token(form_data:OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
    user=crud.get_user_email(db,email=form_data.username)
    if not user or not security.verify_password(form_data.password,user.hash_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect Email or Password"
        )
    access_token_expires=timedelta(minutes=security.ACCESS_TOKEN_EXPIRATION_MINUTES)
    access_token=security.create_access_token(data={"sub":user.email},expires_delta=access_token_expires)
    return {"access_token":access_token,"token_type":"bearer"}


def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    try:
        payload=jwt.decode(token,security.SECURITY_KEY,algorithms=[security.ALGORITHM])
        email: str=payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate Credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate Credentials"
        )
    user=crud.get_user_email(db,email=email)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not Found"
        )
    return user

@router.get("/me",response_model=UserResponse)
def read_users_me(current_user: User=Depends(get_current_user)):
    return current_user
