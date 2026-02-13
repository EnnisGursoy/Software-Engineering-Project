from fastapi import FastAPI
from Backend.Database.connection import engine, Base
from Backend.Models import Employee

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "SQLITE FastAPI Backend is running!"}