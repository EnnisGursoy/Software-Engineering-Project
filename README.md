# PayCentral — Payroll Management System

PayCentral is a full-stack web application for managing employee payroll, time entries, tax information, benefits, and more. It is built with a **FastAPI** backend and a plain **HTML / CSS / JavaScript** frontend backed by a **MySQL** database.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Running the Tests](#running-the-tests)
- [API Overview](#api-overview)
- [Frontend Pages](#frontend-pages)
- [Architecture & Diagrams](#architecture--diagrams)

---

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3.11+, FastAPI, SQLAlchemy   |
| Auth     | JWT (python-jose), Argon2, Fernet   |
| Database | MySQL 8+                            |
| Frontend | HTML5, CSS3, Vanilla JavaScript     |
| Testing  | pytest, SQLite (in-memory)          |

---

## Project Structure

```
Software-Engineering-Project/
├── Backend/
│   ├── Database/        # SQLAlchemy engine & session setup
│   ├── Models/          # ORM models (Employee, User, Paycheck, …)
│   ├── Routes/          # FastAPI routers (Auth, Employee, Payroll, …)
│   ├── Schemas/         # Pydantic request/response schemas
│   ├── Services/        # Business logic layer
│   ├── Utility/         # Security helpers, RBAC dependencies
│   └── main.py          # FastAPI application entry point
├── frontend/            # HTML pages + assets
├── scripts/             # Database setup & helper scripts
├── tests/               # pytest test suite
├── payroll_system.sql   # Full MySQL schema
├── requirements.txt     # Python dependencies
├── DIAGRAMS.md          # ERD, architecture, and flow diagrams (Mermaid)
└── PAYROLL_WORKFLOW.md  # Step-by-step payroll workflow reference
```

---

## Prerequisites

- Python 3.11 or newer
- MySQL 8.0 or newer (running locally or remotely)
- A virtual environment tool (`venv` or `conda`)

---

## Environment Variables

Create a `.env` file in the project root with the following keys:

```env
# MySQL connection string
DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database>

# JWT settings
SECRET_KEY=<a long random hex string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Fernet key for SSN encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=<fernet-key>
```

> **Never commit real credentials.** Add `.env` to `.gitignore` if it is not already there.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/EnnisGursoy/Software-Engineering-Project.git
cd Software-Engineering-Project

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create the database schema
#    Option A — import the provided SQL dump:
mysql -u <user> -p <database> < payroll_system.sql

#    Option B — let SQLAlchemy create the tables automatically on first run
#    (the app calls Base.metadata.create_all on startup)
```

---

## Running the Application

```bash
# Start the FastAPI server (with auto-reload for development)
uvicorn Backend.main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API documentation is available at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc:       <http://localhost:8000/redoc>

To view the **frontend**, open any of the HTML files in the `frontend/` folder directly in your browser, or serve them with a simple static file server:

```bash
# e.g. using Python's built-in server
cd frontend
python -m http.server 5500
# then open http://localhost:5500
```

---

## Running the Tests

The test suite uses **pytest** with an in-memory SQLite database, so no MySQL connection is required:

```bash
pytest
```

To see verbose output:

```bash
pytest -v
```

---

## API Overview

| Tag             | Prefix           | Description                              |
|-----------------|------------------|------------------------------------------|
| Authentication  | `/auth`          | Login, token refresh                     |
| Employee        | `/employee`      | Create, read, update, delete employees   |
| Department      | `/department`    | Manage departments                       |
| Payroll         | `/payroll`       | Run payroll, view paychecks              |
| Time Entries    | `/timeentries`   | Log, approve, and delete time entries    |
| Tax Information | `/tax`           | Employee W-4 / tax settings              |
| Positions       | `/positions`     | Job positions and pay rates              |
| Pay Periods     | `/payperiods`    | Create and close pay periods             |
| Benefits        | `/benefits`      | Benefit plans and enrollments            |

Full interactive docs are auto-generated by FastAPI at `/docs`.

---

## Frontend Pages

| File                 | Description                        |
|----------------------|------------------------------------|
| `index.html`         | Public landing page                |
| `login.html`         | User login                         |
| `homepage.html`      | Main dashboard (post-login)        |
| `employees.html`     | Employee management                |
| `payroll.html`       | Payroll processing                 |
| `shifts.html`        | Time entry / shift management      |
| `taxes.html`         | Tax information                    |
| `benefits.html`      | Benefits enrollment                |
| `positions.html`     | Job positions                      |
| `reports.html`       | Reports                            |
| `profile.html`       | User profile                       |
| `settings.html`      | Application settings               |
| `logout.html`        | Logout                             |

---

## Architecture & Diagrams

Detailed Mermaid diagrams covering the ERD, system architecture, payroll processing flow, authentication flow, and component dependency map are available in:

- [`DIAGRAMS.md`](DIAGRAMS.md)
- [`PAYROLL_WORKFLOW.md`](PAYROLL_WORKFLOW.md)
