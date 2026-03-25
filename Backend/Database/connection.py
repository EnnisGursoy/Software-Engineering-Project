from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=False)  # env vars already set (e.g. Railway) take priority

# Railway MySQL plugin sets MYSQL_URL automatically; fall back to DATABASE_URL or .env
DATABASE_URL = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# Create engine and session
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()

