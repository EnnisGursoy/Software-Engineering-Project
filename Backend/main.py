import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.Database.connection import engine, Base
from Backend.Routes import Auth, Employee, department
from Backend.Routes import Payroll, TimeEntries, TaxInformation, Positions, PayPeriods, Benefits

app = FastAPI(title="PAY CENTRAL API", version="1.0.0", description="API for managing employee data in Pay Central")

# ALLOWED_ORIGINS env var: comma-separated list of frontend origins.
# Falls back to localhost defaults for local dev.
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if _origins_env:
    _origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
else:
    _origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(Auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(Employee.router, prefix="/employee", tags=["Employee"])
app.include_router(department.router, prefix="/department", tags=["Department"])
app.include_router(Payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(TimeEntries.router, prefix="/timeentries", tags=["Time Entries"])
app.include_router(TaxInformation.router, prefix="/tax", tags=["Tax Information"])
app.include_router(Positions.router, prefix="/positions", tags=["Positions"])
app.include_router(PayPeriods.router, prefix="/payperiods", tags=["Pay Periods"])
app.include_router(Benefits.router, prefix="/benefits", tags=["Benefits"])
