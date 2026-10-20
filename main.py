from fastapi import FastAPI

from app.routes import users, products, resume


app = FastAPI(
    title="AI Resume Parser API",
    description="FastAPI backend with Gemini AI integration",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(products.router)
app.include_router(resume.router)


@app.get("/")
def home():
    return {"message": "AI Resume Parser API is running"}
