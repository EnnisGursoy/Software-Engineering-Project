from sqlalchemy.orm import Session
from fastapi import HTTPException
from Backend.Models.Employee import Employee
from cryptography.fernet import Fernet
import re



STRICT_SSN_REGEX = r"^(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}$"


def validate_name(first: str, last: str, db: Session):
    existing = (
        db.query(Employee)
        .filter(Employee.first_name == first, Employee.last_name == last)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Employee with this name already exists"
        )




def validate_ssn_format(ssn: str):
    if not re.match(STRICT_SSN_REGEX, ssn):
        raise HTTPException(
            status_code=400,
            detail="Invalid SSN format or invalid number range."
        )



def encrypt_ssn(ssn : str):
    

