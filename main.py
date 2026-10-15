from fastapi import FastAPI
import random
from pydantic import BaseModel,EmailStr


class ProductModel(BaseModel):
    name:str
    price:float
    color:str

class UserModel(BaseModel):
    name:str
    email:EmailStr
    age:int

app=FastAPI()
users_db={}

@app.get("/")
def hello_message():
    return{"message": "hello Fast Api"}

@app.get("/users")
def get_users_all():
    return users_db

@app.get("/users/{user_id}")
def get_specific_user(user_id:int):
    return users_db.get(user_id, {"error":"user not found"})

@app.post("/users")
def create_users(userData:UserModel):
    user_id=random.randint(1000,9999)
    while user_id in users_db:
        user_id=random.randint(1000,9999)
    users_db[user_id]=userData
    return {"message":"User has been created Successfully","user_id":user_id}

@app.put("/user/{user_id}")
def update_user(user_id:int,userData:UserModel):
    if user_id not in users_db:
        return {"Error":"This user does not exits"}
    users_db[user_id]=userData
    return {"message":"User has been updated Successfully","user_id":user_id}


@app.delete("/user/{user_id}")
def delete_user(user_id:int):
    if user_id not in users_db:
        return {"Error":"This user does not exits"}
    del users_db[user_id]
    return {"message":"User has been updated Successfully"}

@app.post("/products")
def create_products(product:ProductModel):
    return {"message":"Product Created Successfull","name":product.name,"price":product.price,"color":product.color}
    
