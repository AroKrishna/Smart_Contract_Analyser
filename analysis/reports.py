"""
analysis/reports.py - Exportable Audit Report Generation (Phase 7)

Generates professional standard executive reports:
- PDF Audit Reports via reportlab
- Editable DOCX Reports via python-docx

Report Structure:
Executive Summary -> Overall Risk Score -> Category Breakdown ->
AI Recommendations -> Full Compliance Matrix -> Legal Disclaimer
"""

import io
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def generate_pdf_report(audit: Dict[str, Any]) -> bytes:
    """Generates an executive PDF audit report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a")
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )

    story = []

    # Title & Metadata Header
    story.append(Paragraph("Smart Contract Analyser — Legal AI Audit Report", title_style))
    story.append(Spacer(1, 4))
    contract_name = audit.get("contractName") or audit.get("name") or "Contract"
    analysis_id = audit.get("analysisId") or audit.get("id") or "N/A"
    audit_date = audit.get("auditDate") or audit.get("timestamp") or "N/A"
    risk_score = audit.get("riskScore") or audit.get("overallRiskScore") or 0
    risk_level = audit.get("riskLevel") or audit.get("overallRiskLevel") or "Low"

    meta_text = (
        f"<b>Contract:</b> {contract_name} &nbsp;|&nbsp; "
        f"<b>Audit ID:</b> {analysis_id} &nbsp;|&nbsp; "
        f"<b>Date:</b> {audit_date}"
    )
    story.append(Paragraph(meta_text, body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10, spaceBefore=6))

    # Executive Summary & Risk Badge
    story.append(Paragraph("1. Executive Summary & Overall Risk Score", h2_style))
    summary_text = audit.get("summary") or "Automated legal-risk assessment completed."
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 6))

    score_data = [
        ["Overall Risk Score", f"{risk_score} / 100", f"Classification: {risk_level} Risk"],
        ["Analysis Model", audit.get("metadata", {}).get("engineType", "Legal-BERT Neural Classifier"), "Operational Hazard Scope"]
    ]
    score_table = Table(score_data, colWidths=[150, 150, 230])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # 5 Risk Categories Breakdown
    story.append(Paragraph("2. Risk Categories Breakdown (5 Core Taxonomies)", h2_style))
    cat_headers = ["Category", "Severity Level", "Score", "Evaluated Summary"]
    cat_rows = [cat_headers]

    for cat in audit.get("categories", []):
        cat_rows.append([
            cat.get("name", ""),
            cat.get("severity") or cat.get("riskLevel", "Low"),
            f"{cat.get('score', 0)}/100",
            cat.get("summary", "")[:75] + ("..." if len(cat.get("summary", "")) > 75 else "")
        ])

    if len(cat_rows) > 1:
        cat_table = Table(cat_rows, colWidths=[120, 80, 50, 280])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(cat_table)
    story.append(Spacer(1, 10))

    # Compliance Matrix
    story.append(Paragraph("3. Statutory Compliance Consideration Matrix", h2_style))
    matrix_headers = ["Regulatory Framework", "Status", "Assessment Note"]
    matrix_rows = [matrix_headers]

    for item in audit.get("complianceMatrix", []):
        matrix_rows.append([
            item.get("area", ""),
            item.get("status", "Pass"),
            item.get("note", "")
        ])

    if len(matrix_rows) > 1:
        matrix_table = Table(matrix_rows, colWidths=[150, 60, 320])
        matrix_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(matrix_table)
    story.append(Spacer(1, 14))

    # Disclaimer
    story.append(Paragraph("Legal & Non-Equivalence Notice", h2_style))
    disclaimer = (
        "This automated report provides technical and operational legal-hazard decision support "
        "derived from machine learning classification models. Findings reflect syntactic capabilities and "
        "governance patterns. They DO NOT constitute authoritative legal opinions, formal statutory advice, "
        "or guarantees of judicial enforceability under any specific jurisdiction."
    )
    story.append(Paragraph(disclaimer, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_docx_report(audit: Dict[str, Any]) -> bytes:
    """Generates an editable Word DOCX audit report."""
    doc = docx.Document()

    # Title
    title = doc.add_heading("Smart Contract Analyser — Legal AI Audit Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    contract_name = audit.get("contractName") or audit.get("name") or "Contract"
    analysis_id = audit.get("analysisId") or audit.get("id") or "N/A"
    audit_date = audit.get("auditDate") or audit.get("timestamp") or "N/A"
    risk_score = audit.get("riskScore") or audit.get("overallRiskScore") or 0
    risk_level = audit.get("riskLevel") or audit.get("overallRiskLevel") or "Low"

    # Metadata Paragraph
    p_meta = doc.add_paragraph()
    p_meta.add_run(f"Contract: {contract_name} | Audit ID: {analysis_id} | Date: {audit_date}\n").bold = True
    p_meta.add_run(f"Overall Risk Score: {risk_score}/100 ({risk_level} Risk)").bold = True

    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph(audit.get("summary") or "Automated analysis completed.")

    doc.add_heading("2. Risk Categories Breakdown (5 Core Taxonomies)", level=1)
    categories = audit.get("categories", [])
    if categories:
        table = doc.add_table(rows=1, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Category"
        hdr_cells[1].text = "Severity"
        hdr_cells[2].text = "Score"
        hdr_cells[3].text = "Evaluated Summary"

        for cat in categories:
            row_cells = table.add_row().cells
            row_cells[0].text = cat.get("name", "")
            row_cells[1].text = cat.get("severity") or cat.get("riskLevel", "Low")
            row_cells[2].text = f"{cat.get('score', 0)}/100"
            row_cells[3].text = cat.get("summary", "")

    doc.add_heading("3. Statutory Compliance Matrix", level=1)
    matrix = audit.get("complianceMatrix", [])
    if matrix:
        table = doc.add_table(rows=1, cols=3)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Regulatory Area"
        hdr_cells[1].text = "Assessment Status"
        hdr_cells[2].text = "Evaluated Note"

        for item in matrix:
            row_cells = table.add_row().cells
            row_cells[0].text = item.get("area", "")
            row_cells[1].text = item.get("status", "Pass")
            row_cells[2].text = item.get("note", "")

    doc.add_heading("4. Legal Disclaimer", level=1)
    disclaimer = (
        "This automated report provides technical and operational legal-hazard decision support "
        "derived from machine learning classification models. Findings reflect syntactic capabilities and "
        "governance patterns. They DO NOT constitute authoritative legal opinions, formal statutory advice, "
        "or guarantees of judicial enforceability under any specific jurisdiction."
    )
    p_disc = doc.add_paragraph(disclaimer)
    p_disc.runs[0].italic = True

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
