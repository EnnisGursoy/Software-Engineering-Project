from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os 
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from decouple import config   




load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
ENCRYPTION_KEY = config("ENCRYPTION_KEY").encode()
fernet = Fernet(ENCRYPTION_KEY)


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool: 
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    



def encrypt_ssn(ssn : str) -> str :
    return fernet.encrypt(ssn.encode()).decode()

def decrypt_ssn(encrypted_ssn : str) -> str :
    return fernet.decrypt(encrypted_ssn.encode()).decode()