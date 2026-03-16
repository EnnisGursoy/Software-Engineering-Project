# Pay Central — System Diagrams

---

## 1. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USER {
        int user_id PK
        string username
        string password_hash
        string first_name
        string last_name
        enum role "admin | manager | hr"
        bool is_active
        datetime created_at
        datetime updated_at
    }

    DEPARTMENT {
        int department_id PK
        string department_name
        int manager_id FK
    }

    EMPLOYEE {
        int employee_id PK
        string first_name
        string last_name
        string email
        string phone
        string address
        string city
        string state
        string zip_code
        date date_of_birth
        date hire_date
        date termination_date
        string ssn "encrypted"
        enum employment_status "active | terminated | on_leave"
        int department_id FK
    }

    POSITION {
        int position_id PK
        string position_title
        decimal base_salary
        decimal hourly_rate
        enum employment_type "full_time | part_time | contract"
        int department_id FK
    }

    EMPLOYEE_POSITION {
        int emp_position_id PK
        int employee_id FK
        int position_id FK
        decimal current_salary
        decimal current_hourly_rate
        enum pay_frequency "weekly | bi_weekly | semi_monthly | monthly"
        date start_date
        date end_date
        bool is_current
    }

    PAY_PERIOD {
        int pay_period_id PK
        date period_start_date
        date period_end_date
        date pay_date
        enum period_type "weekly | bi_weekly | semi_monthly | monthly"
        enum status "open | processing | paid | closed"
    }

    PAYCHECK {
        int paycheck_id PK
        int employee_id FK
        int pay_period_id FK
        string check_number
        decimal gross_pay
        decimal net_pay
        decimal federal_tax
        decimal state_tax
        decimal social_security
        decimal medicare
        decimal health_insurance
        decimal retirement_401k
        decimal other_deductions
        enum payment_method "direct_deposit | check | cash"
        enum payment_status "pending | processed | paid | void"
        date payment_date
    }

    TIME_ENTRY {
        int entry_id PK
        int employee_id FK
        int approved_by FK
        date entry_date
        time clock_in
        time clock_out
        decimal regular_hours
        decimal overtime_hours
        enum entry_type "work | sick | vacation | holiday | unpaid"
        string notes
        bool approved
    }

    TAX_INFORMATION {
        int tax_id PK
        int employee_id FK
        enum filing_status "single | married | head_of_household"
        int federal_allowances
        int state_allowances
        decimal additional_withholding
        bool exempt_federal
        bool exempt_state
        date effective_date
    }

    DEPARTMENT ||--o{ EMPLOYEE : "employs"
    DEPARTMENT ||--o| EMPLOYEE : "managed by"
    DEPARTMENT ||--o{ POSITION : "has"
    EMPLOYEE ||--o{ EMPLOYEE_POSITION : "holds"
    POSITION ||--o{ EMPLOYEE_POSITION : "filled by"
    EMPLOYEE ||--o{ PAYCHECK : "receives"
    PAY_PERIOD ||--o{ PAYCHECK : "contains"
    EMPLOYEE ||--o{ TIME_ENTRY : "logs"
    EMPLOYEE ||--o{ TIME_ENTRY : "approves"
    EMPLOYEE ||--o| TAX_INFORMATION : "has"
```

---

## 2. System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (HTML/CSS/JS)"]
        Login[login.html]
        Dashboard[index.html]
        Employees[employees.html]
        Payroll[payroll.html]
        Shifts[shifts.html]
        Taxes[taxes.html]
        Reports[reports.html]
        Profile[profile.html]
    end

    subgraph Backend["Backend (FastAPI)"]
        subgraph Routes["Routes Layer"]
            AuthR["/auth"]
            EmpR["/employee"]
            DeptR["/department"]
            PayR["/payroll"]
            TimeR["/timeentries"]
            TaxR["/tax"]
            PeriodR["/pay-periods"]
        end

        subgraph Services["Services Layer"]
            EmpS[employee_service]
            PayS[paycheck_service]
            TimeS[timeentry_service]
            DeptS[department_service]
            PeriodS[payperiod_service]
            PosS[position_service]
            TaxS[tax_service]
        end

        subgraph Utility["Utility"]
            Security[security.py\nJWT · Argon2 · Fernet]
            Deps[dependencies.py\nRBAC · DI]
        end

        subgraph Models["ORM Models (SQLAlchemy)"]
            M1[Employee]
            M2[Department]
            M3[Position]
            M4[Paycheck]
            M5[TimeEntry]
            M6[TaxInfo]
            M7[PayPeriod]
            M8[User]
        end
    end

    subgraph DB["Database (MySQL)"]
        Tables[(Tables)]
    end

    Frontend -->|HTTP / JSON| Routes
    Routes --> Services
    Routes --> Utility
    Services --> Models
    Models --> DB
```

---

## 3. Payroll Processing Flow

```mermaid
flowchart TD
    A([Start]) --> B[HR creates Pay Period\nstart_date · end_date · pay_date]
    B --> C[Employees log Time Entries\nclock_in / clock_out / entry_type]
    C --> D[Manager reviews Time Entries]
    D --> E{Approved?}
    E -- No --> F[Return to Employee\nfor correction]
    F --> C
    E -- Yes --> G[HR runs Payroll\nPOST /payroll/run/period_id]
    G --> H[System fetches active employees\n+ approved time entries]
    H --> I[Calculate Gross Pay\nhourly_rate × regular_hours\n+ hourly_rate × 1.5 × overtime_hours]
    I --> J[Apply Tax Deductions]
    J --> J1[Federal Tax\nbrackets 10%–37%\nminus W-4 allowances]
    J --> J2[State Tax\n5% flat rate]
    J --> J3[Social Security 6.2%\nMedicare 1.45%]
    J --> J4[Health Insurance\n401k · Other]
    J1 & J2 & J3 & J4 --> K[Compute Net Pay\nnet = gross − all deductions]
    K --> L[Create Paycheck record\nstatus: pending]
    L --> M[HR updates status → processed]
    M --> N[Payment issued\nstatus → paid]
    N --> O([End])
```

---

## 4. Authentication & Role-Based Access Control

```mermaid
flowchart LR
    User([User]) -->|POST /auth/login\nusername + password| Auth[Auth Route]
    Auth -->|Verify password\nArgon2| DB[(Users Table)]
    DB --> Auth
    Auth -->|Issue JWT\nrole claim embedded| User

    User -->|Request + Bearer token| Protected[Protected Route]
    Protected --> Decode[Decode & verify JWT]
    Decode --> RoleCheck{Role Check}

    RoleCheck -->|admin| AdminOps["Full access:\ndelete users\nclose pay periods\nmanage departments"]
    RoleCheck -->|hr| HROps["HR access:\ncreate/update employees\nprocess payroll\napprove time entries\nmanage tax info"]
    RoleCheck -->|manager| ManagerOps["Manager access:\nview department\napprove time entries\nview payroll"]
    RoleCheck -->|Unauthorized| Deny[403 Forbidden]
```

---

## 5. Component Dependency Map

```mermaid
graph LR
    subgraph R["Routes"]
        AR[Auth]
        ER[Employee]
        DR[Department]
        PR[Payroll]
        TR[TimeEntries]
        XR[Tax]
        PPR[PayPeriods]
    end

    subgraph S["Services"]
        ES[employee_service]
        PS[paycheck_service]
        TS[timeentry_service]
        DS[department_service]
        PPS[payperiod_service]
        POS[position_service]
        XS[tax_service]
    end

    subgraph M["Models"]
        EM[Employee]
        DM[Department]
        PM[Position]
        PCM[Paycheck]
        TM[TimeEntry]
        XM[TaxInfo]
        PPM[PayPeriod]
        UM[User]
        EPM[EmployeePosition]
    end

    ER --> ES
    PR --> PS
    TR --> TS
    DR --> DS
    PPR --> PPS
    XR --> XS

    ES --> EM & DM & EPM
    PS --> PCM & EM & PPM & TM & XM & EPM
    TS --> TM & EM
    DS --> DM & EM
    PPS --> PPM
    POS --> PM & EPM
    XS --> XM & EM
```
