
import random

from fastapi import APIRouter, HTTPException
from app.models.schemas import UserModel
from app.database import users_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("")
def get_users_all():
    return users_db


@router.get("/{user_id}")
def get_specific_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return users_db[user_id]


@router.post("")
def create_user(userData: UserModel):
    user_id = random.randint(1000, 9999)

    while user_id in users_db:
        user_id = random.randint(1000, 9999)

    users_db[user_id] = userData

    return {
        "message": "User created successfully",
        "user_id": user_id
    }


@router.put("/{user_id}")
def update_user(user_id: int, userData: UserModel):
    if user_id not in users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    users_db[user_id] = userData

    return {
        "message": "User updated successfully",
        "user_id": user_id
    }


@router.delete("/{user_id}")
def delete_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    del users_db[user_id]

    return {
        "message": "User deleted successfully"
    }
