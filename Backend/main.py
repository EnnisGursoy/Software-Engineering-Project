from fastapi import FastAPI
from Backend.Database.connection import engine, Base
from Backend.Routes import Auth, Employee



app = FastAPI(Title = "PAY CENTRAL API", version = "1.0.0", description = "API for managing employee data in Pay Central")

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(Auth.router, prefix = "/auth", tags=["Authentication"])
app.include_router(Employee.router, prefix = "/employee", tags=["Employee"])