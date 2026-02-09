"""
Payroll Functions
Tax calculations, gross pay, and utility functions.
All business logic lives here in Python instead of SQL stored functions.
"""

from decimal import Decimal, ROUND_HALF_UP
from db_connection import execute_query

# --- Constants ---

SS_WAGE_BASE = Decimal("168600.00")
SS_RATE = Decimal("0.0620")
MEDICARE_RATE = Decimal("0.0145")
MEDICARE_ADDITIONAL_RATE = Decimal("0.0090")
MEDICARE_THRESHOLD = Decimal("200000.00")
ALLOWANCE_AMOUNT = Decimal("4300.00")

PAY_PERIODS_PER_YEAR = {
    "weekly": 52,
    "bi_weekly": 26,
    "semi_monthly": 24,
    "monthly": 12,
}

# Simplified flat state tax rates
STATE_TAX_RATES = {
    "CA": Decimal("0.0725"),
    "NY": Decimal("0.0685"),
    "TX": Decimal("0.0000"),
    "FL": Decimal("0.0000"),
    "IL": Decimal("0.0495"),
    "AZ": Decimal("0.0250"),
    "WA": Decimal("0.0000"),
    "NV": Decimal("0.0000"),
    "PA": Decimal("0.0307"),
    "OH": Decimal("0.0400"),
}
DEFAULT_STATE_RATE = Decimal("0.0500")

# 2024 Federal tax brackets
FEDERAL_BRACKETS_SINGLE = [
    (Decimal("11600"), Decimal("0.10"), Decimal("0")),
    (Decimal("47150"), Decimal("0.12"), Decimal("1160")),
    (Decimal("100525"), Decimal("0.22"), Decimal("5426")),
    (Decimal("191950"), Decimal("0.24"), Decimal("17168.50")),
    (Decimal("243725"), Decimal("0.32"), Decimal("39110.50")),
    (Decimal("609350"), Decimal("0.35"), Decimal("55758.50")),
    (None, Decimal("0.37"), Decimal("183647.25")),
]

FEDERAL_BRACKETS_MARRIED = [
    (Decimal("23200"), Decimal("0.10"), Decimal("0")),
    (Decimal("94300"), Decimal("0.12"), Decimal("2320")),
    (Decimal("201050"), Decimal("0.22"), Decimal("10852")),
    (Decimal("383900"), Decimal("0.24"), Decimal("34337")),
    (Decimal("487450"), Decimal("0.32"), Decimal("78221")),
    (Decimal("731200"), Decimal("0.35"), Decimal("111357")),
    (None, Decimal("0.37"), Decimal("196669.50")),
]


def _round(value):
    """Round to 2 decimal places using standard rounding."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# --- Tax Calculation Functions ---

def calculate_social_security(gross_pay, ytd_gross):
    """
    Calculates Social Security tax.
    6.2% of gross pay, up to the annual wage base ($168,600).
    """
    gross_pay = Decimal(str(gross_pay))
    ytd_gross = Decimal(str(ytd_gross))

    if ytd_gross >= SS_WAGE_BASE:
        return Decimal("0.00")

    if (ytd_gross + gross_pay) > SS_WAGE_BASE:
        taxable = SS_WAGE_BASE - ytd_gross
    else:
        taxable = gross_pay

    return _round(taxable * SS_RATE)


def calculate_medicare(gross_pay, ytd_gross):
    """
    Calculates Medicare tax.
    1.45% on all earnings, plus additional 0.9% on earnings over $200k.
    """
    gross_pay = Decimal(str(gross_pay))
    ytd_gross = Decimal(str(ytd_gross))

    tax = _round(gross_pay * MEDICARE_RATE)
    new_ytd = ytd_gross + gross_pay

    if new_ytd > MEDICARE_THRESHOLD:
        if ytd_gross >= MEDICARE_THRESHOLD:
            tax += _round(gross_pay * MEDICARE_ADDITIONAL_RATE)
        else:
            tax += _round((new_ytd - MEDICARE_THRESHOLD) * MEDICARE_ADDITIONAL_RATE)

    return tax


def calculate_federal_tax(gross_pay, pay_frequency, filing_status,
                          allowances=0, additional_withholding=0, exempt=False):
    """
    Calculates federal income tax using simplified 2024 brackets.
    Annualizes the gross pay, applies brackets, then converts back to per-period.
    """
    if exempt:
        return Decimal("0.00")

    gross_pay = Decimal(str(gross_pay))
    additional_withholding = Decimal(str(additional_withholding))
    periods_per_year = PAY_PERIODS_PER_YEAR.get(pay_frequency, 26)

    annual_income = gross_pay * periods_per_year
    taxable = annual_income - (allowances * ALLOWANCE_AMOUNT)

    if taxable <= 0:
        return _round(additional_withholding)

    if filing_status == "married":
        brackets = FEDERAL_BRACKETS_MARRIED
    else:
        brackets = FEDERAL_BRACKETS_SINGLE

    annual_tax = Decimal("0.00")
    prev_limit = Decimal("0")

    for limit, rate, base_tax in brackets:
        if limit is None or taxable <= limit:
            annual_tax = base_tax + (taxable - prev_limit) * rate
            break
        prev_limit = limit

    per_period_tax = _round(annual_tax / periods_per_year)
    return per_period_tax + additional_withholding


def calculate_state_tax(gross_pay, state, allowances=0, exempt=False):
    """
    Calculates state income tax using simplified flat rates.
    Some states (TX, FL, WA, NV) have no income tax.
    """
    if exempt:
        return Decimal("0.00")

    gross_pay = Decimal(str(gross_pay))
    rate = STATE_TAX_RATES.get(state, DEFAULT_STATE_RATE)

    # Reduce slightly per allowance
    rate = max(rate - (allowances * Decimal("0.005")), Decimal("0"))

    return _round(gross_pay * rate)


# --- Pay Calculation Functions ---

def get_pay_periods_per_year(frequency):
    """Returns the number of pay periods per year for a given frequency."""
    return PAY_PERIODS_PER_YEAR.get(frequency, 26)


def calculate_employee_gross_pay(employee_id, period_start, period_end):
    """
    Calculates gross pay for an employee in a pay period.
    - Salaried: annual salary / number of pay periods
    - Hourly: (regular hours * rate) + (overtime hours * rate * 1.5)
    """
    position = execute_query(
        """SELECT current_salary, current_hourly_rate, pay_frequency
           FROM employee_positions
           WHERE employee_id = %s AND is_current = 1
           LIMIT 1""",
        (employee_id,),
        fetch=True,
    )

    if not position:
        return Decimal("0.00")

    pos = position[0]
    salary = pos["current_salary"]
    hourly_rate = pos["current_hourly_rate"]
    frequency = pos["pay_frequency"]

    if salary and salary > 0:
        periods = get_pay_periods_per_year(frequency)
        return _round(Decimal(str(salary)) / periods)

    if hourly_rate and hourly_rate > 0:
        hours = execute_query(
            """SELECT COALESCE(SUM(regular_hours), 0) AS reg,
                      COALESCE(SUM(overtime_hours), 0) AS ot
               FROM time_entries
               WHERE employee_id = %s
                 AND entry_date BETWEEN %s AND %s
                 AND approved = 1""",
            (employee_id, period_start, period_end),
            fetch=True,
        )
        reg = Decimal(str(hours[0]["reg"]))
        ot = Decimal(str(hours[0]["ot"]))
        rate = Decimal(str(hourly_rate))
        return _round((reg * rate) + (ot * rate * Decimal("1.5")))

    return Decimal("0.00")


def get_ytd_gross(employee_id, year):
    """Returns the year-to-date gross pay for an employee (excludes voided checks)."""
    result = execute_query(
        """SELECT COALESCE(SUM(pc.gross_pay), 0) AS ytd
           FROM paychecks pc
           JOIN pay_periods pp ON pc.pay_period_id = pp.pay_period_id
           WHERE pc.employee_id = %s
             AND YEAR(pp.period_start_date) = %s
             AND pc.payment_status != 'void'""",
        (employee_id, year),
        fetch=True,
    )
    return Decimal(str(result[0]["ytd"]))
