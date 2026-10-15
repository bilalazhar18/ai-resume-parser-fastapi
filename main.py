from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def hello_message():
    return{"message": "hello Fast Api"}