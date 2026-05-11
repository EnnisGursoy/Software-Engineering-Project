"""
Pay-stub PDF renderer.

Builds a printable, single-page pay stub from a Paychecks row plus its
related Employee and PayPeriod records. Returns raw PDF bytes so the
caller can stream them straight back over HTTP.

We use reportlab's high-level platypus API: it takes care of layout,
page breaks, and font metrics so the route stays small.
"""

from io import BytesIO
from datetime import date
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Models.Paychecks import Paychecks
from Backend.Models.Employee import Employee
from Backend.Models.pay_periods import PayPeriods


# Brand colors — match the blue used throughout the frontend
BRAND_BLUE = colors.HexColor("#1d4ed8")
SOFT_GREY = colors.HexColor("#f1f5f9")
BORDER_GREY = colors.HexColor("#d1d5db")
TEXT_DARK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#6b7280")


def _money(value: float | None) -> str:
    return f"${float(value or 0):,.2f}"


def _fmt_date(d: date | None) -> str:
    return d.strftime("%b %d, %Y") if d else "—"


def _meta_table(employee: Employee, paycheck: Paychecks, period: PayPeriods | None) -> Table:
    """Two-column employee / pay-period header block."""
    full_name = f"{employee.first_name} {employee.last_name}"
    period_range = (
        f"{_fmt_date(period.period_start_date)} – {_fmt_date(period.period_end_date)}"
        if period else f"Period #{paycheck.pay_period_id}"
    )
    rows = [
        ["Employee:", full_name, "Pay Period:", period_range],
        ["Employee ID:", str(employee.employee_id), "Pay Date:",
         _fmt_date(period.pay_date if period else paycheck.payment_date)],
        ["Email:", employee.email or "—", "Check #:",
         paycheck.check_number or str(paycheck.paycheck_id)],
        ["Address:", _format_address(employee), "Status:",
         (paycheck.payment_status or "pending").title()],
    ]
    t = Table(rows, colWidths=[1.0 * inch, 2.4 * inch, 1.0 * inch, 2.4 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("TEXTCOLOR", (3, 0), (3, -1), TEXT_DARK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _format_address(emp: Employee) -> str:
    parts = [emp.address, emp.city, emp.state, emp.zip_code]
    line = ", ".join(p for p in parts if p)
    return line or "—"


def _amount_table(title: str, rows: Iterable[tuple[str, float | None]],
                  total_label: str, total_value: float) -> Table:
    """Earnings or Deductions block with a bottom-row total."""
    body = [[title, "Amount"]]
    for label, value in rows:
        body.append([label, _money(value)])
    body.append([total_label, _money(total_value)])

    t = Table(body, colWidths=[4.4 * inch, 2.4 * inch])
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), SOFT_GREY),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # Body
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -2), TEXT_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#fafbfc")]),
        # Total row
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, BORDER_GREY),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fafbfc")),
        # Cell padding
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Outer border
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
    ]))
    return t


def _net_pay_box(net_pay: float) -> Table:
    t = Table([["Net Pay", _money(net_pay)]], colWidths=[4.4 * inch, 2.4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def render_paystub_pdf(
    paycheck: Paychecks,
    employee: Employee,
    period: PayPeriods | None,
) -> bytes:
    """
    Build a one-page pay stub PDF and return it as bytes.

    Caller is responsible for fetching the three records (paycheck +
    employee + pay period) and for any access-control checks.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"Pay Stub #{paycheck.check_number or paycheck.paycheck_id}",
        author="PayCentral",
    )

    styles = getSampleStyleSheet()
    company_style = ParagraphStyle(
        "Company", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=22, textColor=BRAND_BLUE,
        alignment=1, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=MUTED,
        alignment=1, spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=10, textColor=TEXT_DARK,
        spaceBefore=10, spaceAfter=4,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=8, textColor=MUTED,
        alignment=1, spaceBefore=20,
    )

    # Tax totals are split into "income tax" and "FICA" lines on most
    # real stubs, so mirror that here.
    fed = paycheck.federal_tax or 0
    state = paycheck.state_tax or 0
    ss = paycheck.social_security or 0
    medicare = paycheck.medicare or 0
    health = paycheck.health_insurance or 0
    retirement = paycheck.retirement_401k or 0
    other = paycheck.other_deductions or 0
    total_deductions = fed + state + ss + medicare + health + retirement + other

    story = [
        Paragraph("PayCentral", company_style),
        Paragraph("EARNINGS STATEMENT &nbsp;•&nbsp; PAY STUB", subtitle_style),
        _meta_table(employee, paycheck, period),
        Spacer(1, 0.18 * inch),

        Paragraph("Earnings", section_style),
        _amount_table(
            "Description",
            [("Regular / Salary", paycheck.gross_pay)],
            "Gross Pay",
            paycheck.gross_pay or 0,
        ),
        Spacer(1, 0.10 * inch),

        Paragraph("Taxes", section_style),
        _amount_table(
            "Tax",
            [
                ("Federal Income Tax", fed),
                ("State Income Tax", state),
                ("Social Security (6.2%)", ss),
                ("Medicare (1.45%)", medicare),
            ],
            "Total Taxes",
            fed + state + ss + medicare,
        ),
        Spacer(1, 0.10 * inch),

        Paragraph("Other Deductions", section_style),
        _amount_table(
            "Description",
            [
                ("Health Insurance", health),
                ("401(k) Retirement", retirement),
                ("Other Deductions", other),
            ],
            "Total Other Deductions",
            health + retirement + other,
        ),
        Spacer(1, 0.10 * inch),

        Paragraph("Summary", section_style),
        _amount_table(
            "Item",
            [
                ("Gross Pay", paycheck.gross_pay),
                ("Total Deductions", total_deductions),
            ],
            "Net Pay (Take-Home)",
            paycheck.net_pay or 0,
        ),
        Spacer(1, 0.16 * inch),

        _net_pay_box(paycheck.net_pay or 0),

        Paragraph(
            "This document is an electronic pay stub generated by PayCentral. "
            "Retain for your records.",
            footer_style,
        ),
    ]

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
