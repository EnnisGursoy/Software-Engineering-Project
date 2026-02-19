from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Backend.Database.connection import SessionLocal

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to the Authentication API!"}