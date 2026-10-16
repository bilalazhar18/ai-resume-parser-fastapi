
from pydantic import BaseModel, EmailStr


class UserModel(BaseModel):
    name: str
    email: EmailStr
    age: int


class ProductModel(BaseModel):
    name: str
    price: float
    color: str


class ResumeTextModel(BaseModel):
    resume_text: str
