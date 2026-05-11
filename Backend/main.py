import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.Database.connection import engine, Base, SessionLocal
from Backend.Routes import Auth, Employee, department
from Backend.Routes import Payroll, TimeEntries, TaxInformation, Positions, PayPeriods, Benefits
from Backend.Models.Department import Department
from Backend.Models.BenefitPlan import BenefitPlan

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
        "http://127.0.0.1:5501",
        "http://localhost:5501",
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


def _seed_default_departments() -> None:
    """One-time seed of common departments so the Add Employee dropdown is
    populated on a fresh database. No-op if any departments already exist."""
    db = SessionLocal()
    try:
        if db.query(Department).count() > 0:
            return
        defaults = ["Administration", "Engineering", "Human Resources", "Sales", "Operations"]
        db.add_all([Department(department_name=name) for name in defaults])
        db.commit()
    finally:
        db.close()


_seed_default_departments()


def _seed_default_benefit_plans() -> None:
    """One-time seed of common benefit plans so HR/employees see something
    on the Benefits page on a fresh database. No-op if any plans already
    exist. Costs are illustrative monthly figures."""
    db = SessionLocal()
    try:
        if db.query(BenefitPlan).count() > 0:
            return
        defaults = [
            # Health
            BenefitPlan(plan_name="Aetna PPO Standard", plan_type="Health",
                        provider="Aetna", employee_cost=150.00, employer_cost=450.00,
                        coverage_level="Individual",
                        notes="Nationwide PPO network; $1,500 deductible."),
            BenefitPlan(plan_name="Aetna PPO Family", plan_type="Health",
                        provider="Aetna", employee_cost=400.00, employer_cost=900.00,
                        coverage_level="Family",
                        notes="Family PPO; $3,000 deductible, dependents covered."),
            BenefitPlan(plan_name="BlueCross HMO Basic", plan_type="Health",
                        provider="BlueCross BlueShield", employee_cost=90.00, employer_cost=300.00,
                        coverage_level="Individual",
                        notes="In-network HMO; lower premium, referrals required."),
            # Dental
            BenefitPlan(plan_name="Delta Dental Basic", plan_type="Dental",
                        provider="Delta Dental", employee_cost=20.00, employer_cost=45.00,
                        coverage_level="Individual",
                        notes="Preventive 100%, basic 80%, major 50%."),
            BenefitPlan(plan_name="Delta Dental Plus Family", plan_type="Dental",
                        provider="Delta Dental", employee_cost=55.00, employer_cost=110.00,
                        coverage_level="Family",
                        notes="Family coverage incl. orthodontia for dependents under 19."),
            # Vision
            BenefitPlan(plan_name="VSP Vision", plan_type="Vision",
                        provider="VSP", employee_cost=10.00, employer_cost=15.00,
                        coverage_level="Individual",
                        notes="Annual exam, $150 frame allowance, lens benefits."),
            # Life
            BenefitPlan(plan_name="MetLife Basic Life ($50K)", plan_type="Life",
                        provider="MetLife", employee_cost=0.00, employer_cost=25.00,
                        coverage_level="Individual",
                        notes="Employer-paid term life, $50,000 face value."),
            BenefitPlan(plan_name="MetLife Voluntary Life ($250K)", plan_type="Life",
                        provider="MetLife", employee_cost=35.00, employer_cost=0.00,
                        coverage_level="Individual",
                        notes="Optional supplemental term life, employee-paid."),
            # Retirement
            BenefitPlan(plan_name="Fidelity 401(k) Traditional", plan_type="Retirement",
                        provider="Fidelity", employee_cost=0.00, employer_cost=0.00,
                        coverage_level="Individual",
                        notes="Pre-tax contributions; employer match up to 5% of salary."),
            BenefitPlan(plan_name="Fidelity Roth 401(k)", plan_type="Retirement",
                        provider="Fidelity", employee_cost=0.00, employer_cost=0.00,
                        coverage_level="Individual",
                        notes="After-tax Roth contributions; same 5% employer match."),
        ]
        db.add_all(defaults)
        db.commit()
    finally:
        db.close()


_seed_default_benefit_plans()


app.include_router(Auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(Employee.router, prefix="/employee", tags=["Employee"])
app.include_router(department.router, prefix="/department", tags=["Department"])
app.include_router(Payroll.router, prefix="/payroll", tags=["Payroll"])
app.include_router(TimeEntries.router, prefix="/timeentries", tags=["Time Entries"])
app.include_router(TaxInformation.router, prefix="/tax", tags=["Tax Information"])
app.include_router(Positions.router, prefix="/positions", tags=["Positions"])
app.include_router(PayPeriods.router, prefix="/payperiods", tags=["Pay Periods"])
app.include_router(Benefits.router, prefix="/benefits", tags=["Benefits"])
