from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import users as crud
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.session import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


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
