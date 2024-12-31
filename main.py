from fastapi import FastAPI
from app import chatAi, cover_letter_generator, resume_review

app = FastAPI()
app.include_router(chatAi.router, tags=["ChatAI"])
app.include_router(cover_letter_generator.router, tags=["Cover Letter Generator"])
app.include_router(resume_review.router, tags=["Resume Review Generator"])

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}