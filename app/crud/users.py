from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate
from app import security

class DuplicateEmailError(ValueError):
    """A user already owns this email address."""


def _save(db: Session, user: User) -> User:
    email = user.email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if get_user_email(db, email) is not None:
            raise DuplicateEmailError("Email already exists") from None
        raise
    db.refresh(user)
    return user


def create_user(db: Session, user: UserCreate) -> User:
    pwd_password=security.get_password_hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        hash_password=pwd_password,
    )
    db.add(db_user)
    return _save(db, db_user)


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_all(db: Session) -> list[User]:
    return db.query(User).all()


def user_update(db: Session, user_id: int, user_data: UserUpdate) -> User | None:
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
    db_user.name = user_data.name
    db_user.email = user_data.email
    if user_data.password is not None:
        db_user.hash_password = security.get_password_hash(user_data.password)
    return _save(db, db_user)


def delete_user(db: Session, user_id: int) -> User | None:
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user
