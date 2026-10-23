"""
analysis/reports.py - Exportable Audit Report Generation (Phase 7)

Generates professional standard executive reports:
- PDF Audit Reports via reportlab
- Editable DOCX Reports via python-docx

Report Structure:
Executive Summary -> Overall Risk Score -> Category Breakdown ->
Highlighted Risky Clauses -> Explainable AI (XAI) Attributions ->
AI Recommendations -> Statutory Compliance Matrix -> Legal Disclaimer
"""

import io
from typing import Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def generate_pdf_report(audit: Dict[str, Any]) -> bytes:
    """Generates an executive PDF audit report with risk, findings, XAI, and recommendations."""
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
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    code_style = ParagraphStyle(
        "CodeSnip",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
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
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8, spaceBefore=5))

    # 1. Executive Summary & Risk Badge
    story.append(Paragraph("1. Executive Summary & Overall Risk Score", h2_style))
    summary_text = audit.get("summary") or "Automated legal-risk assessment completed."
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 6))

    score_data = [
        ["Overall Risk Score", f"{risk_score} / 100", f"Classification: {risk_level} Risk"],
        ["Analysis Engine", audit.get("metadata", {}).get("engineType", "Legal-BERT Neural Classifier"), "Operational Legal Hazard Scope"]
    ]
    score_table = Table(score_data, colWidths=[140, 140, 250])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8))

    # 2. Risk Categories Breakdown
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
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(cat_table)
    story.append(Spacer(1, 8))

    # 3. Highlighted Risky Clauses & Findings
    story.append(Paragraph("3. Highlighted Risky Clauses & Static Findings", h2_style))
    findings = audit.get("findings", [])
    if findings:
        f_headers = ["Category", "Severity", "Lines", "Finding Description & Snippet"]
        f_rows = [f_headers]
        for f in findings[:6]:
            line_str = f"L{f.get('lineStart', 1)}-L{f.get('lineEnd', 1)}"
            snip = (f.get("snippet", "") or "").strip().replace("\n", " ")
            snip_preview = f"Snippet: {snip[:80]}..." if len(snip) > 80 else (f"Snippet: {snip}" if snip else "")
            desc = f"{f.get('description', '')} {snip_preview}".strip()
            f_rows.append([
                f.get("category", "General"),
                f.get("severity", "Medium"),
                line_str,
                desc[:140] + ("..." if len(desc) > 140 else "")
            ])

        f_table = Table(f_rows, colWidths=[100, 65, 55, 310])
        f_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(f_table)
    else:
        story.append(Paragraph("No critical syntactic anomalies detected in source scan.", body_style))
    story.append(Spacer(1, 8))

    # 4. Explainable AI (XAI) Attribution Highlights
    story.append(Paragraph("4. Explainable AI (XAI) Attribution Highlights", h2_style))
    shap_vals = audit.get("shapValues", [])
    lime_vals = audit.get("limeExplanations", [])

    xai_rows = [["Method", "Attributed Token / Feature", "Risk Contribution", "Direction"]]
    if isinstance(shap_vals, list):
        for item in shap_vals[:4]:
            tok = item.get("token") or item.get("feature") or str(item)
            w = item.get("weight") or item.get("score") or 0.0
            direction = "Risk Escalation (+)" if w >= 0 else "Risk Reduction (-)"
            xai_rows.append(["SHAP", str(tok), f"{w:+.4f}" if isinstance(w, (int, float)) else str(w), direction])

    if isinstance(lime_vals, list):
        for item in lime_vals[:3]:
            tok = item.get("token") or item.get("feature") or str(item)
            w = item.get("weight") or item.get("score") or 0.0
            direction = "Risk Escalation (+)" if w >= 0 else "Risk Reduction (-)"
            xai_rows.append(["LIME", str(tok), f"{w:+.4f}" if isinstance(w, (int, float)) else str(w), direction])

    if len(xai_rows) > 1:
        xai_table = Table(xai_rows, colWidths=[80, 190, 120, 140])
        xai_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(xai_table)
    else:
        story.append(Paragraph("Attribution weights distributed across standard EVM opcode sequences.", body_style))
    story.append(Spacer(1, 8))

    # 5. AI Recommendations
    recs = audit.get("recommendations", [])
    if recs:
        story.append(Paragraph("5. AI Recommendations & Remediations", h2_style))
        rec_rows = [["Priority", "Category", "Issue & Recommended Remediation"]]
        for r in recs[:5]:
            prio = r.get("priority", "Medium")
            cat = r.get("category", "General")
            issue_rec = f"{r.get('issue', '')} -> {r.get('recommendation', '')}"
            rec_rows.append([prio, cat, issue_rec[:150] + ("..." if len(issue_rec) > 150 else "")])

        rec_table = Table(rec_rows, colWidths=[70, 110, 350])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 8))

    # 6. Compliance Matrix
    story.append(Paragraph("6. Statutory Compliance Consideration Matrix", h2_style))
    matrix_headers = ["Regulatory Framework", "Status", "Assessment Note"]
    matrix_rows = [matrix_headers]

    for item in audit.get("complianceMatrix", []):
        matrix_rows.append([
            item.get("area", ""),
            item.get("status", "Pass"),
            item.get("note", "")[:120] + ("..." if len(item.get("note", "")) > 120 else "")
        ])

    if len(matrix_rows) > 1:
        matrix_table = Table(matrix_rows, colWidths=[140, 60, 330])
        matrix_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(matrix_table)
    story.append(Spacer(1, 10))

    # 7. Disclaimer
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
    """Generates an editable Word DOCX audit report with risk, findings, XAI, and recommendations."""
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

    # 1. Executive Summary
    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph(audit.get("summary") or "Automated analysis completed.")

    # 2. Risk Categories Breakdown
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

    # 3. Highlighted Risky Clauses & Findings
    findings = audit.get("findings", [])
    if findings:
        doc.add_heading("3. Highlighted Risky Clauses & Static Findings", level=1)
        f_table = doc.add_table(rows=1, cols=4)
        f_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        f_hdr = f_table.rows[0].cells
        f_hdr[0].text = "Category"
        f_hdr[1].text = "Severity"
        f_hdr[2].text = "Lines"
        f_hdr[3].text = "Finding Description & Snippet"

        for f in findings[:8]:
            row_cells = f_table.add_row().cells
            row_cells[0].text = f.get("category", "")
            row_cells[1].text = f.get("severity", "")
            row_cells[2].text = f"L{f.get('lineStart', 1)}-L{f.get('lineEnd', 1)}"
            snip = (f.get("snippet", "") or "").strip().replace("\n", " ")
            snip_preview = f" [Snippet: {snip[:80]}...]" if len(snip) > 80 else (f" [Snippet: {snip}]" if snip else "")
            row_cells[3].text = f"{f.get('description', '')}{snip_preview}"

    # 4. Explainable AI (XAI) Attribution Highlights
    shap_vals = audit.get("shapValues", [])
    lime_vals = audit.get("limeExplanations", [])
    if shap_vals or lime_vals:
        doc.add_heading("4. Explainable AI (XAI) Attribution Highlights", level=1)
        xai_table = doc.add_table(rows=1, cols=4)
        xai_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        x_hdr = xai_table.rows[0].cells
        x_hdr[0].text = "Framework"
        x_hdr[1].text = "Token / Syntactic Feature"
        x_hdr[2].text = "Attribution Weight"
        x_hdr[3].text = "Impact Direction"

        if isinstance(shap_vals, list):
            for item in shap_vals[:5]:
                row = xai_table.add_row().cells
                row[0].text = "SHAP"
                row[1].text = str(item.get("token") or item.get("feature") or item)
                w = item.get("weight") or item.get("score") or 0.0
                row[2].text = f"{w:+.4f}" if isinstance(w, (int, float)) else str(w)
                row[3].text = "Risk Escalation (+)" if (isinstance(w, (int, float)) and w >= 0) else "Risk Reduction (-)"

        if isinstance(lime_vals, list):
            for item in lime_vals[:5]:
                row = xai_table.add_row().cells
                row[0].text = "LIME"
                row[1].text = str(item.get("token") or item.get("feature") or item)
                w = item.get("weight") or item.get("score") or 0.0
                row[2].text = f"{w:+.4f}" if isinstance(w, (int, float)) else str(w)
                row[3].text = "Risk Escalation (+)" if (isinstance(w, (int, float)) and w >= 0) else "Risk Reduction (-)"

    # 5. AI Recommendations
    recs = audit.get("recommendations", [])
    if recs:
        doc.add_heading("5. AI Recommendations & Remediations", level=1)
        r_table = doc.add_table(rows=1, cols=3)
        r_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        r_hdr = r_table.rows[0].cells
        r_hdr[0].text = "Priority"
        r_hdr[1].text = "Category"
        r_hdr[2].text = "Issue & Recommended Remediation"

        for r in recs[:6]:
            row = r_table.add_row().cells
            row[0].text = r.get("priority", "Medium")
            row[1].text = r.get("category", "General")
            row[2].text = f"{r.get('issue', '')} -> {r.get('recommendation', '')}"

    # 6. Compliance Matrix
    doc.add_heading("6. Statutory Compliance Matrix", level=1)
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

    # 7. Legal Disclaimer
    doc.add_heading("7. Legal Disclaimer", level=1)
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
