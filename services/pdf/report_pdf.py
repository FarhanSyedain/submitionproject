"""Render an analysis Report as a downloadable PDF."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def render_report_pdf(report) -> bytes:
    """Build a multi-section PDF from a Report and return raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=report.title or "Zeaniv report",
    )

    styles = _styles()
    story: list = []

    business = report.business
    session = report.session

    # ── Cover ────────────────────────────────────────────────────────────
    story.append(Paragraph("Zeaniv Analysis Report", styles["Title"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(business.name, styles["Subtitle"]))
    if business.industry:
        story.append(Paragraph(business.industry, styles["Meta"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#3b82f6")))
    story.append(Spacer(1, 0.25 * inch))

    # ── Executive summary ────────────────────────────────────────────────
    if report.executive_summary:
        story.append(Paragraph("Executive Summary", styles["H1"]))
        story.append(Paragraph(report.executive_summary, styles["Body"]))
        story.append(Spacer(1, 0.2 * inch))

    # ── Key insights ────────────────────────────────────────────────────
    if report.key_insights:
        story.append(Paragraph("Key Insights", styles["H1"]))
        for insight in report.key_insights:
            story.append(Paragraph(f"• {insight}", styles["Bullet"]))
        story.append(Spacer(1, 0.2 * inch))

    # ── Recommended actions ──────────────────────────────────────────────
    if report.recommended_actions:
        story.append(Paragraph("Recommended Actions", styles["H1"]))
        rows = [["Priority", "Action", "Timeline"]]
        for item in report.recommended_actions:
            rows.append(
                [
                    str(item.get("priority", "")).title(),
                    str(item.get("action", "")),
                    str(item.get("timeline", "")),
                ]
            )
        table = Table(rows, colWidths=[1 * inch, 4 * inch, 1.7 * inch])
        table.setStyle(_action_table_style())
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    # ── Top ideas ────────────────────────────────────────────────────────
    top_ideas = list(
        session.ideas.exclude(overall_score=None).order_by("-overall_score")[:5]
    )
    if top_ideas:
        story.append(PageBreak())
        story.append(Paragraph("Top Ideas", styles["H1"]))
        for idea in top_ideas:
            score_text = f" — score {idea.overall_score}" if idea.overall_score else ""
            story.append(Paragraph(f"{idea.title}{score_text}", styles["H2"]))
            if idea.description:
                story.append(Paragraph(idea.description, styles["Body"]))
            verdict = ""
            try:
                verdict = idea.validation.verdict.replace("_", " ").title()
            except Exception:
                pass
            if verdict:
                story.append(Paragraph(f"Verdict: <b>{verdict}</b>", styles["Meta"]))
            story.append(Spacer(1, 0.15 * inch))

    # ── Competitors snapshot ─────────────────────────────────────────────
    competitors = list(session.competitors.all()[:5])
    if competitors:
        story.append(PageBreak())
        story.append(Paragraph("Competitor Snapshot", styles["H1"]))
        rows = [["Name", "Position", "Threat", "Opportunity Gap"]]
        for c in competitors:
            rows.append(
                [
                    c.name,
                    c.market_position.title() if c.market_position else "",
                    str(c.threat_level),
                    c.opportunity_gap[:120],
                ]
            )
        table = Table(rows, colWidths=[1.5 * inch, 1 * inch, 0.7 * inch, 3.5 * inch])
        table.setStyle(_competitor_table_style())
        story.append(table)

    # ── Trends snapshot ──────────────────────────────────────────────────
    trends = list(session.trends.all()[:5])
    if trends:
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("Trends Snapshot", styles["H1"]))
        for t in trends:
            story.append(
                Paragraph(
                    f"<b>{t.title}</b> &nbsp; <font color='#666'>({t.momentum})</font>",
                    styles["Body"],
                )
            )
            if t.opportunity:
                story.append(Paragraph(f"Opportunity: {t.opportunity}", styles["Meta"]))
            story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer.getvalue()


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0a0f1e"),
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#3b82f6"),
            spaceAfter=4,
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#666666"),
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            textColor=colors.HexColor("#0a0f1e"),
            spaceAfter=8,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontSize=11,
            leading=15,
            leftIndent=12,
            spaceAfter=4,
        ),
    }


def _action_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a0f1e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f9")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _competitor_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a0f1e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f9")]),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ]
    )
