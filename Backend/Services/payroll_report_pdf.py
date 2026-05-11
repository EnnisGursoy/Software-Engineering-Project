"""
Payroll summary report PDF renderer (FR-15).

Renders a multi-row landscape report listing every paycheck for the
selected filters (pay period + payment status), with per-row totals and
a generated-on footer. Mirrors the columns shown in reports.html so the
PDF lines up with the on-screen table.

Caller is responsible for fetching paychecks + employees + periods and
applying the same filter logic the UI uses. This module only formats.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Iterable, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# Match the pay stub brand colours so reports feel like the same product
BRAND_BLUE = colors.HexColor("#1d4ed8")
SOFT_GREY = colors.HexColor("#f1f5f9")
BORDER_GREY = colors.HexColor("#d1d5db")
TEXT_DARK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#6b7280")
ROW_ALT = colors.HexColor("#fafbfc")


def _money(v) -> str:
    return f"${float(v or 0):,.2f}"


def _make_header(filter_text: str) -> list:
    """Top-of-page block: title, filter context, generation timestamp."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=BRAND_BLUE,
        alignment=0, spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=MUTED, spaceAfter=2,
    )
    filt_style = ParagraphStyle(
        "Filter", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=10, textColor=TEXT_DARK,
        spaceAfter=12,
    )
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return [
        Paragraph("PayCentral — Payroll Summary Report", title_style),
        Paragraph(f"Generated {generated_at}", sub_style),
        Paragraph(f"Filter: {filter_text}", filt_style),
    ]


def _make_table(rows: Sequence[dict], totals: dict) -> Table:
    """Build the main data table including a totals row at the bottom."""
    header = ["Employee", "Period", "Gross", "Fed Tax", "State Tax",
              "FICA", "Other Ded.", "Net Pay", "Status"]
    body = [header]
    for r in rows:
        body.append([
            r["employee"],
            r["period"],
            _money(r["gross"]),
            _money(r["fed"]),
            _money(r["state"]),
            _money(r["fica"]),
            _money(r["other"]),
            _money(r["net"]),
            (r["status"] or "—").title(),
        ])
    body.append([
        f"Totals  ({len(rows)} rec.)",
        "",
        _money(totals["gross"]),
        _money(totals["fed"]),
        _money(totals["state"]),
        _money(totals["fica"]),
        _money(totals["other"]),
        _money(totals["net"]),
        "",
    ])

    col_widths = [1.6 * inch, 1.5 * inch, 0.9 * inch, 0.85 * inch, 0.85 * inch,
                  0.85 * inch, 0.95 * inch, 0.95 * inch, 0.7 * inch]
    t = Table(body, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (2, 0), (7, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, 0), 6),
        ("RIGHTPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        # Body
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 8),
        ("TEXTCOLOR", (0, 1), (-1, -2), TEXT_DARK),
        ("ALIGN", (2, 1), (7, -2), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, ROW_ALT]),
        ("LEFTPADDING", (0, 1), (-1, -2), 6),
        ("RIGHTPADDING", (0, 1), (-1, -2), 6),
        ("TOPPADDING", (0, 1), (-1, -2), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 4),
        # Totals row
        ("BACKGROUND", (0, -1), (-1, -1), SOFT_GREY),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 8.5),
        ("ALIGN", (2, -1), (7, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, BORDER_GREY),
        ("TOPPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        # Outer grid
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, BORDER_GREY),
    ])
    t.setStyle(style)
    return t


def render_payroll_report_pdf(
    rows: Iterable[dict],
    totals: dict,
    filter_text: str = "All paychecks",
) -> bytes:
    """
    Build a landscape PDF of the payroll summary report.

    Parameters
    ----------
    rows : iterable of dicts with keys:
        employee, period, gross, fed, state, fica, other, net, status
    totals : dict with keys gross, fed, state, fica, other, net
    filter_text : human-readable filter description for the header

    Returns
    -------
    bytes — raw PDF, ready to stream as application/pdf
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(LETTER),
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title="Payroll Summary Report",
        author="PayCentral",
    )

    rows = list(rows)
    story = []
    story.extend(_make_header(filter_text))
    if not rows:
        styles = getSampleStyleSheet()
        story.append(Paragraph(
            "No paychecks match the current filters.",
            ParagraphStyle("Empty", parent=styles["Normal"],
                           fontName="Helvetica-Oblique",
                           fontSize=10, textColor=MUTED),
        ))
    else:
        story.append(_make_table(rows, totals))
        story.append(Spacer(1, 0.18 * inch))
        styles = getSampleStyleSheet()
        story.append(Paragraph(
            f"{len(rows)} record(s). All amounts in USD.",
            ParagraphStyle("Footer", parent=styles["Normal"],
                           fontName="Helvetica-Oblique",
                           fontSize=8, textColor=MUTED),
        ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
