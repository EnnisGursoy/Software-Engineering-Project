from fastapi import FastAPI
from Backend.Database.connection import engine, Base
from Backend.Models import Employee

app = FastAPI(Title = "PAY CENTRAL API", version = "1.0.0", description = "API for managing employee data in Pay Central")

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "MYSQL FastAPI Backend is running!"}