from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.Database.connection import engine, Base
from Backend.Routes import Auth, Employee, department, tax, pay_periods
from Backend.Routes import Payroll, TimeEntries

app = FastAPI(title="PAY CENTRAL API", version="1.0.0", description="API for managing employee data in Pay Central")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(Auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(Employee.router, prefix="/employee", tags=["Employee"])
app.include_router(department.router, prefix="/department", tags=["Department"])
app.include_router(tax.router, prefix="/tax", tags=["Tax"])
app.include_router(Payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(TimeEntries.router, prefix="/timeentries", tags=["Time Entries"])
app.include_router(pay_periods.router, prefix="/pay-periods", tags=["Pay Periods"])
