"""
scripts/generate_walkthrough_pdf.py - Comprehensive PDF Generator for Smart_Contract_Analyser
Generates: docs/PROJECT_THEORY_AND_CODE_WALKTHROUGH.pdf
Conforms strictly to project codebase, specifications, and verified experimental reports.
"""

import os
import sys
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
    Image as RLImage,
    PageBreak,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count:
    'Page X of Y', running headers, and running footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Skip headers on cover page (page 1)
        if self._pageNumber > 1:
            # Running header
            self.drawString(
                36,
                letter[1] - 30,
                "Smart Contract Analyser — Complete Theory & Code Walkthrough (Final Local Edition)"
            )
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 34, letter[0] - 36, letter[1] - 34)

            # Running footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 36, 24, page_text)
            self.drawString(
                36,
                24,
                "Confidential / Academic Review — Automated Operational Legal-Risk Assessment"
            )
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 34, letter[0] - 36, 34)

        self.restoreState()


def generate_architecture_diagram(output_path: str):
    """Generates a high-resolution, modern architecture diagram for Section 3."""
    fig, ax = plt.subplots(figsize=(10.5, 6.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Background canvas
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    # Title
    ax.text(
        50, 97.2,
        "Smart Contract Analyser — System Architecture & Layered Boundaries",
        ha="center", va="center", fontsize=13, fontweight="bold", color="#0f172a"
    )
    ax.text(
        50, 94.0,
        "Local Loopback Edition: React 19 / Vite Frontend (5173) ↔ FastAPI Backend (8000) ↔ Legal-BERT v3.3.0 Engine",
        ha="center", va="center", fontsize=8.5, color="#475569"
    )

    def draw_box(x, y, w, h, title, items, header_bg="#1e293b", body_bg="#ffffff", border="#cbd5e1", line_gap=3.3):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
            facecolor=body_bg, edgecolor=border, linewidth=1.2
        )
        ax.add_patch(rect)
        hdr = patches.FancyBboxPatch(
            (x, y + h - 5.0), w, 5.0, boxstyle="round,pad=0.2,rounding_size=1.0",
            facecolor=header_bg, edgecolor="none"
        )
        ax.add_patch(hdr)
        ax.text(
            x + w/2, y + h - 2.5, title, ha="center", va="center",
            fontsize=8.2, fontweight="bold", color="#ffffff"
        )
        line_y = y + h - 7.8
        for it in items:
            ax.text(x + 2.0, line_y, it, ha="left", va="center", fontsize=6.8, color="#334155")
            line_y -= line_gap

    # Top Row: Presentation Layer, API Gateway, AI Core (y = 51, h = 40)
    draw_box(
        3, 51, 28, 40,
        "1. PRESENTATION LAYER (React 19 / Vite)",
        [
            "• App Router (React Router v7):",
            "  /dashboard, /analysis/new, /analysis/:id",
            "  /history, /reports, /settings",
            "• Public No-Login Local Workspace",
            "• Monospace Solidity Viewer (CodeViewer)",
            "  Gutter badges, line-highlighting",
            "• Explainability Panels (XAI):",
            "  ShapChart (Token impact bars)",
            "  LimeExplanation (Linear surrogate)",
            "• Scoped Legal Assistant (Chat UI)",
            "• PDF & DOCX Export Triggers",
            "• Dual-target API Client (api.js)"
        ],
        header_bg="#2563eb", body_bg="#ffffff", border="#93c5fd", line_gap=3.1
    )

    draw_box(
        35, 51, 29, 40,
        "2. API & SECURITY GATEWAY (FastAPI)",
        [
            "• Loopback Binding (127.0.0.1:8000)",
            "• DNS Rebinding Check (Host validation)",
            "• Cross-Site Request Defense (Sec-Fetch)",
            "• Sliding-Window Rate Limiter (20/min)",
            "• Payload Size Enforcer (<= 1MB)",
            "• Ephemeral In-Memory Store (LRU 100)",
            "• Background Async Job Stepper:",
            "  Validating ➔ Parsing ➔ Inferring ➔",
            "  Attributing ➔ Synthesizing ➔ Done",
            "• Job Idempotency & Duplicate Guards",
            "• Job Cancellation & Interruption Reconcile"
        ],
        header_bg="#0f172a", body_bg="#ffffff", border="#94a3b8", line_gap=3.1
    )

    draw_box(
        68, 51, 29, 40,
        "3. AI & INFERENCE CORE (Legal-BERT)",
        [
            "• Solidity AST & Regex Parser (No solc):",
            "  Extracts AST, NatSpec, functions, vars",
            "• Dual-Stream Context Synthesizer:",
            "  Observable code + documented intent",
            "• Fine-Tuned Legal-BERT v3.3.0 Checkpoint:",
            "  Multi-label sequence classification",
            "  5 Sigmoid heads (threshold = 0.50)",
            "• XAI Mathematical Engines:",
            "  - SHAP: shap.Explainer permutations",
            "  - LIME: Local linear surrogate regressions",
            "  - Saliency: PyTorch autograd Input x Grad",
            "• Grounded Chat Engine (AST + findings)"
        ],
        header_bg="#4f46e5", body_bg="#ffffff", border="#a5b4fc", line_gap=3.1
    )

    # Bottom Row: Storage & Compliance (y = 5, h = 38)
    draw_box(
        8, 6, 40, 36,
        "4. LOCAL STORAGE & PERSISTENCE (SQLite)",
        [
            "• SQLite Database: transient_smart_contract_analyser.db",
            "• Relational Tables: analyses, jobs, stored_files, users, audit_logs",
            "• Local Sandboxed Storage: backend/data/storage/local_user/",
            "• Path Traversal Defense & Safe Filename Sanitization",
            "• Automatic 30-Day Retention Daemon (Periodic cleanup worker)",
            "• Complete Purge Cascade (Deletes DB rows and disk files)"
        ],
        header_bg="#059669", body_bg="#ffffff", border="#6ee7b7", line_gap=4.8
    )

    draw_box(
        52, 6, 40, 36,
        "5. COMPLIANCE, REPORTING & EXTENSIONS",
        [
            "• ReportLab PDF Generator (Executive audit report)",
            "• python-docx DOCX Generator (Editable findings doc)",
            "• Statutory Compliance Matrix (GDPR, Consumer Law, Fairness)",
            "• Side-by-side Remediation Synthesizer (Before / After)",
            "• Context-Grounded Legal Assistant (Query scoping)",
            "• Optional OpenAI-Compatible LLM Integration (with offline fallback)"
        ],
        header_bg="#d97706", body_bg="#ffffff", border="#fcd34d", line_gap=4.8
    )

    # Connective arrows
    ax.annotate(
        "", xy=(35, 71), xytext=(31, 71),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#2563eb")
    )
    ax.text(33, 73, "HTTP", fontsize=7.2, ha="center", color="#2563eb", fontweight="bold")

    ax.annotate(
        "", xy=(68, 71), xytext=(64, 71),
        arrowprops=dict(arrowstyle="->", lw=1.8, color="#4f46e5")
    )
    ax.text(66, 73, "Inference", fontsize=7.2, ha="center", color="#4f46e5", fontweight="bold")

    ax.annotate(
        "", xy=(28, 42), xytext=(45, 51),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#059669")
    )

    ax.annotate(
        "", xy=(72, 42), xytext=(55, 51),
        arrowprops=dict(arrowstyle="->", lw=1.5, color="#d97706")
    )

    plt.tight_layout()
    plt.savefig(output_path, format="png", bbox_inches="tight")
    plt.close()


def generate_sequence_diagram(output_path: str):
    """Generates an end-to-end data flow and sequence diagram for Section 3."""
    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    ax.text(
        50, 96,
        "Smart Contract Analyser — End-to-End Analysis Data Flow & Job Lifecycle",
        ha="center", va="center", fontsize=13, fontweight="bold", color="#0f172a"
    )
    ax.text(
        50, 92.5,
        "Step-by-Step Lifecycle from User Submission to Grounded AI Chat & Report Download",
        ha="center", va="center", fontsize=8.5, color="#475569"
    )

    # Vertical swimlanes
    lanes = [
        ("User / Browser", 10),
        ("React UI (Vite)", 30),
        ("FastAPI Server", 50),
        ("Legal-BERT Core", 70),
        ("SQLite & Storage", 90),
    ]

    for name, lx in lanes:
        # Header box
        hdr = patches.FancyBboxPatch(
            (lx - 8, 84), 16, 5.5, boxstyle="round,pad=0.2,rounding_size=0.8",
            facecolor="#1e293b", edgecolor="none"
        )
        ax.add_patch(hdr)
        ax.text(lx, 86.8, name, ha="center", va="center", fontsize=8, fontweight="bold", color="#ffffff")
        # Vertical lifeline
        ax.plot([lx, lx], [84, 8], color="#cbd5e1", linestyle="--", linewidth=1.0)

    # Step arrows & labels
    steps = [
        (80, 10, 30, "1. Paste code / Drop .sol file", "#2563eb"),
        (72, 30, 50, "2. POST /api/v1/analyze/jobs (Idempotency Key)", "#2563eb"),
        (64, 50, 90, "3. Save physical .sol & create job record ('queued')", "#059669"),
        (56, 50, 70, "4. Dispatch AST parser + Legal-BERT v3.3.0 inference", "#4f46e5"),
        (48, 70, 70, "5. Compute SHAP + LIME + PyTorch Gradient Saliency", "#4f46e5"),
        (40, 70, 50, "6. Return probabilities, findings, XAI, recommendations", "#4f46e5"),
        (32, 50, 90, "7. Persist analysis & update job status ('completed')", "#059669"),
        (24, 30, 50, "8. Poll GET /api/v1/jobs/{id} (1.2s intervals)", "#2563eb"),
        (16, 50, 30, "9. Return complete audit payload ➔ route /analysis/:id", "#2563eb"),
        (9, 30, 10, "10. Render source viewer, XAI bars, chat & PDF export", "#0f172a"),
    ]

    for y, x1, x2, label, col in steps:
        if x1 == x2:
            # Self loop
            ax.annotate(
                "", xy=(x1 + 4, y - 2), xytext=(x1, y + 2),
                arrowprops=dict(arrowstyle="->", lw=1.3, color=col, connectionstyle="arc3,rad=-0.8")
            )
            ax.text(x1 + 7, y, label, ha="left", va="center", fontsize=7.2, color=col, fontweight="bold")
        else:
            ax.annotate(
                "", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="->", lw=1.3, color=col)
            )
            mid_x = (x1 + x2) / 2
            ax.text(mid_x, y + 1.8, label, ha="center", va="bottom", fontsize=7.2, color=col, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, format="png", bbox_inches="tight")
    plt.close()


def build_pdf(output_filename: str):
    """Compiles the complete 9-section PDF walkthrough document."""
    os.makedirs(os.path.dirname(os.path.abspath(output_filename)), exist_ok=True)
    temp_dir = tempfile.gettempdir()
    arch_png = os.path.join(temp_dir, "smart_contract_analyser_arch_temp.png")
    seq_png = os.path.join(temp_dir, "smart_contract_analyser_seq_temp.png")

    print("[1/4] Generating high-resolution architectural and sequence diagrams...")
    generate_architecture_diagram(arch_png)
    generate_sequence_diagram(seq_png)

    print("[2/4] Setting up ReportLab typographic styling and document structure...")
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44,
    )

    base_styles = getSampleStyleSheet()

    # Custom styles
    styles = {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=8,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#334155"),
            spaceAfter=15,
        ),
        "MetaBanner": ParagraphStyle(
            "MetaBanner",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#475569"),
        ),
        "H1": ParagraphStyle(
            "Heading1_Custom",
            parent=base_styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "Heading2_Custom",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "H3": ParagraphStyle(
            "Heading3_Custom",
            parent=base_styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=5,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        ),
        "Callout": ParagraphStyle(
            "Callout_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#1e293b"),
        ),
        "CodeBlock": ParagraphStyle(
            "CodeBlock_Custom",
            parent=base_styles["Code"],
            fontName="Courier",
            fontSize=7.2,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
        ),
        "TableHead": ParagraphStyle(
            "TableHead_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=colors.white,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9.5,
            textColor=colors.HexColor("#1e293b"),
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold_Custom",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9.5,
            textColor=colors.HexColor("#0f172a"),
        ),
        "TableCellCode": ParagraphStyle(
            "TableCellCode_Custom",
            parent=base_styles["Normal"],
            fontName="Courier",
            fontSize=6.8,
            leading=8.5,
            textColor=colors.HexColor("#0f172a"),
        ),
        "BadgeMatches": ParagraphStyle(
            "BadgeMatches",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor("#065f46"),
        ),
        "BadgeDiffers": ParagraphStyle(
            "BadgeDiffers",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor("#991b1b"),
        ),
        "BadgePartial": ParagraphStyle(
            "BadgePartial",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor("#92400e"),
        ),
    }

    story = []

    def make_callout(text, title="NOTE", border_col="#3b82f6", bg_col="#eff6ff", text_col="#1e3a8a"):
        content = [
            Paragraph(f"<b>{title}:</b> {text}", ParagraphStyle("callout_inner", parent=styles["Callout"], textColor=colors.HexColor(text_col)))
        ]
        t = Table([[content]], colWidths=[letter[0] - 72])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_col)),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor(border_col)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    def make_code_box(code_str, filename, line_range, symbol=""):
        header_text = f"<b>File:</b> <code>{filename}</code> &nbsp;|&nbsp; <b>Lines:</b> {line_range}"
        if symbol:
            header_text += f" &nbsp;|&nbsp; <b>Symbol:</b> <code>{symbol}</code>"
        
        escaped_code = code_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>").replace(" ", "&nbsp;")
        
        table_data = [
            [Paragraph(header_text, ParagraphStyle("code_hdr", parent=styles["TableCellBold"], fontSize=7.2, textColor=colors.HexColor("#0f172a")))],
            [Paragraph(escaped_code, styles["CodeBlock"])]
        ]
        t = Table(table_data, colWidths=[letter[0] - 72])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        # Keep entire code snippet together so header is never orphaned
        return KeepTogether(t)

    # =========================================================================
    # COVER / TITLE BANNER
    # =========================================================================
    story.append(Paragraph("Smart Contract Analyser", styles["CoverTitle"]))
    story.append(Paragraph("Comprehensive Project Theory, Architectural Foundations & Actual Code Implementation Walkthrough", styles["CoverSubtitle"]))
    
    meta_box = [
        [
            Paragraph(
                "<b>Authoritative Specification:</b> <code>docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx</code><br/>"
                "<b>Active Release Target:</b> Final Local Edition (Downloadable Offline Academic & Auditor Application)<br/>"
                "<b>Verified Codebase:</b> Git branch <code>main</code> (Clean Working Tree, 87/87 Automated Tests Passing)<br/>"
                "<b>Model Checkpoint:</b> <code>analysis/models/legal_bert_v3.3.0/</code> (Multi-Label Classifier, 438 MB SafeTensors)<br/>"
                "<b>Canonical Dataset:</b> <code>data/ml_candidates/final_dataset.jsonl</code> (v3.3.0, SHA-256: <code>74464fd132...</code>)<br/>"
                "<b>Evaluation Runtime:</b> Python 3.14.3 (FastAPI 0.115+, PyTorch 2.11+, Pytest 9.1+) | React 19.2 (Vite 8.3, Tailwind v4)",
                styles["MetaBanner"]
            )
        ]
    ]
    t_meta = Table(meta_box, colWidths=[letter[0] - 72])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#94a3b8")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Academic Notice Callout
    notice_text = (
        "This technical document provides an exhaustive, evidence-verified walkthrough of the finalized Smart_Contract_Analyser "
        "system. It presents both the theoretical computer-science and legal-informatics foundations and the exact, active code "
        "implementation. Every architectural claim, line number, API contract, and benchmark metric has been verified directly "
        "against current repository source files. In strict accordance with platform ethics and university research guidelines, "
        "this tool is designed for operational legal-risk triaging; it does not replace qualified legal counsel or certified security audits."
    )
    story.append(make_callout(notice_text, title="ACADEMIC & OPERATIONAL NOTICE", border_col="#2563eb", bg_col="#eff6ff", text_col="#1e3a8a"))
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: PROJECT OVERVIEW AND INTENDED SCOPE
    # =========================================================================
    story.append(Paragraph("1. Project Overview and Intended Scope", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("1.1 The Operational Risk Problem in Smart Contracts", styles["H2"]))
    story.append(Paragraph(
        "Over the past decade, smart-contract auditing has focused almost exclusively on <i>runtime execution security</i>—detecting "
        "reentrancy vectors, integer overflows, unhandled exceptions, oracle front-running, and flash-loan vulnerabilities. Tools such as "
        "Slither, Mythril, and Securify analyze whether code can be forced to execute erroneously or out of invariant specifications. "
        "However, a smart contract can execute <b>with 100% mathematical precision and zero security vulnerabilities</b> while still creating "
        "severe legal liabilities, contractual invalidity, statutory violations, or unfair consumer harm.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "Examples of this fundamental divide include unilateral killswitches that forfeit user deposits without notice, uncapped fee "
        "multipliers that permit an operator to arbitrarily siphon liquidity, non-reciprocal exculpatory disclaimers that claim complete immunity "
        "from gross negligence, and the immutable storage of plaintext personal identifiers (PII) on public distributed ledgers in violation of "
        "statutory privacy rights such as the GDPR Article 17 ('Right to Erasure'). <b>Smart_Contract_Analyser</b> solves this problem by "
        "providing automated operational legal-risk assessment and explainability specifically tailored for Solidity contracts.",
        styles["Body"]
    ))

    story.append(Paragraph("1.2 Intended Users and Deployment Architecture", styles["H2"]))
    story.append(Paragraph(
        "The project serves smart-contract developers, independent auditors, legal-engineering researchers, and compliance teams. "
        "Following an architectural pivot for the academic release, the current finalized version is architected as a <b>fully private, "
        "single-user downloadable local application</b>:",
        styles["Body"]
    ))

    # Scope verification bullets
    scope_table_data = [
        [
            Paragraph("<b>Dimension</b>", styles["TableHead"]),
            Paragraph("<b>Specification Requirement</b>", styles["TableHead"]),
            Paragraph("<b>Current Implementation Status (Verified)</b>", styles["TableHead"]),
            Paragraph("<b>Verification Evidence</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Execution Topology", styles["TableCellBold"]),
            Paragraph("Local single-user runtime with optional SaaS hosting.", styles["TableCell"]),
            Paragraph("<b>100% Local Loopback Execution</b>. FastAPI binds strictly to <code>127.0.0.1:8000</code>; Vite UI runs on <code>127.0.0.1:5173</code>.", styles["TableCell"]),
            Paragraph("<code>backend/main.py:259-276</code>; <code>README.md:20-25</code>", styles["TableCellCode"]),
        ],
        [
            Paragraph("Account & Auth Requirements", styles["TableCellBold"]),
            Paragraph("Email/password, Google/GitHub OAuth, session cookies.", styles["TableCell"]),
            Paragraph("<b>Zero Login Required</b> in current release. Direct workspace access; routes <code>/login</code>, <code>/register</code>, <code>/profile</code> redirect to <code>/dashboard</code>.", styles["TableCell"]),
            Paragraph("<code>frontend/src/App.jsx:37-42</code>; <code>backend/main.py:408-424</code>", styles["TableCellCode"]),
        ],
        [
            Paragraph("Data Persistence & Privacy", styles["TableCellBold"]),
            Paragraph("Persistent audit history and contract records.", styles["TableCell"]),
            Paragraph("<b>Local SQLite DB & User Storage</b>. Saved to <code>transient_smart_contract_analyser.db</code> and <code>backend/data/storage/local_user/</code>. Never leaves local disk.", styles["TableCell"]),
            Paragraph("<code>backend/analysis/db.py:26-42</code>; <code>backend/analysis/storage.py:103-125</code>", styles["TableCellCode"]),
        ],
        [
            Paragraph("Network Dependency", styles["TableCellBold"]),
            Paragraph("Cloud API connections for deep learning models.", styles["TableCell"]),
            Paragraph("<b>Fully Offline Execution</b> after initial setup. Neural model and XAI run locally on CPU/GPU. Zero telemetry or external cloud pings.", styles["TableCell"]),
            Paragraph("<code>backend/analysis/engine.py:510-528</code>; <code>README.md:127-129</code>", styles["TableCellCode"]),
        ],
    ]
    t_scope = Table(scope_table_data, colWidths=[100, 130, 180, 130])
    t_scope.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_scope)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.3 Five Project Risk Categories vs. Out-of-Scope Security Hazards", styles["H2"]))
    story.append(Paragraph(
        "The project rigorously categorizes risks across five operational domains defined in <code>docs/ANALYSIS_SPECIFICATION.md</code> "
        "and enforced in <code>backend/analysis/engine.py:34-40</code>:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "1. <b>Privacy</b> (Severity: <i>Critical</i>): On-chain storage of unencrypted Personally Identifiable Information (PII) such as "
        "plaintext emails, phone numbers, or physical addresses, conflicting with statutory rights to erasure and confidentiality.<br/>"
        "2. <b>Termination</b> (Severity: <i>Critical</i>): Unilateral, unconstrained killswitches (<code>selfdestruct</code>, <code>suicide</code>) "
        "or arbitrary operational pauses that destroy contract state or sweep user collateral without counterparty recourse.<br/>"
        "3. <b>Legal Compliance</b> (Severity: <i>High</i>): Centralized administrative privilege concentration without multi-signature or timelock "
        "oversight, statutory disclosure gaps, or non-compliance with commercial transparency requirements.<br/>"
        "4. <b>Liability</b> (Severity: <i>High</i>): Disproportionate contractual indemnification, punitive slashing mechanisms exceeding 100% of collateral, "
        "or blanket NatSpec disclaimers of gross negligence and willful misconduct.<br/>"
        "5. <b>Payment / Financial</b> (Severity: <i>High</i>): Uncapped fee modification setters, arbitrary tax adjustments, or withdrawal lockups "
        "that allow administrators to unilaterally dilute or confiscate user deposits.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "<b>Explicitly Out of Scope:</b> Low-level bytecode execution bugs (EVM call-depth attacks, reentrancy via unchecked external calls, "
        "arithmetic wrap-around in legacy pre-0.8.0 Solidity, miner-extractable value / front-running, and compiler optimization defects) "
        "remain the exclusive domain of formal EVM security analyzers (e.g., Slither). Smart_Contract_Analyser analyzes <b>what the contract "
        "legally empowers administrators to do</b> under normal execution.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: THEORY BEHIND THE SYSTEM
    # =========================================================================
    story.append(Paragraph("2. Theory Behind the System", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("2.1 The Representation Mismatch: Natural-Language Legal Models on Code", styles["H2"]))
    story.append(Paragraph(
        "A foundational insight of this project is that <b>raw Solidity source code cannot be directly fed into standard natural-language "
        "legal transformers</b>. Transformer models like Legal-BERT (Chalkidis et al., 2020) were pre-trained on judicial rulings, statutes, "
        "contracts, and regulatory filings. Their WordPiece vocabularies are optimized for English legal prose. When exposed to raw Solidity syntax "
        "(e.g., <code>mapping(address => uint256)</code>, <code>assembly { extcodesize(addr) }</code>, or <code>nonReentrant</code>), the tokenizer "
        "suffers severe token fragmentation, splitting keywords into arbitrary subwords (e.g., <code>['ext', '##code', '##size']</code>). "
        "Furthermore, syntactic boilerplate (pragmas, memory pointers, typecasts) dilutes the model's 512-token context window without providing "
        "contractual meaning.",
        styles["Body"]
    ))

    story.append(Paragraph("2.2 Dual-Stream Context Formulation: Paired Structure and NatSpec Intent", styles["H2"]))
    story.append(Paragraph(
        "To overcome this representation gap, the system implements a <b>Dual-Stream Observable Representation</b> in "
        "<code>backend/analysis/engine.py:552-606</code> (<code>extract_submission_model_text</code>). At submission time, the Solidity parser extracts "
        "and normalizes two distinct streams into structured natural language:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "• <b>Structural Execution Stream</b>: Evaluates function visibility, administrative access modifiers (<code>onlyOwner</code>, <code>hasRole</code>), "
        "privileged operations (<code>selfdestruct</code>, fee setters, blacklist routines), and state mutations.<br/>"
        "• <b>Semantic Intent Stream</b>: Extracts developer declarations from NatSpec docstrings (<code>@notice</code>, <code>@dev</code>, <code>@param</code>), "
        "inline comments, and license disclosures describing warranties, obligations, and intended behavior.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The synthesized representation passed into Legal-BERT adheres to this strict observable template:",
        styles["Body"]
    ))
    sample_rep = (
        "[Submission Context — Observable Contract Representation]\n"
        "Contract: EscrowSettlement (MIT)\n"
        "Function: emergencyKill (external)\n"
        "Modifiers: onlyOwner\n"
        "Documented Intent: Two-party commercial settlement with owner emergency kill switch.\n"
        "Operational Behavior: Contains termination instruction capable of deleting bytecode and sweeping balance.\n"
        "Key Code Logic: function emergencyKill() external { require(msg.sender == owner); selfdestruct(owner); }"
    )
    story.append(make_code_box(sample_rep, "backend/analysis/engine.py", "597-606", "extract_submission_model_text"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.3 Legal-BERT Architecture & Multi-Label Classification Mechanics", styles["H2"]))
    story.append(Paragraph(
        "The neural core is based on <code>nlpaueb/legal-bert-base-uncased</code> (110M parameters, 12 layers, 768 hidden dimensions, 12 attention heads). "
        "In this project, the model performs <b>Multi-Label Sequence Classification</b>. It does <i>not</i> perform single-label or multi-class "
        "classification, because a single smart-contract function can simultaneously exhibit multiple operational hazards (e.g., both an arbitrary "
        "termination killswitch and an uncapped fee confiscation routine).",
        styles["Body"]
    ))
    story.append(Paragraph(
        "The classifier architecture attaches a linear classification head (<code>model.classifier</code>) to the pooled <code>[CLS]</code> token embedding, "
        "producing 5 independent raw logits $z_1, z_2, z_3, z_4, z_5$. Each logit is transformed into an independent operational probability via the "
        "standard logistic sigmoid function:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "$$\\sigma(z_i) = \\frac{1}{1 + e^{-z_i}} \\in [0, 1] \\quad \\text{for } i \\in \\{1, 2, 3, 4, 5\\}$$",
        styles["BodyBold"]
    ))
    story.append(Paragraph(
        "During training, the loss is computed using <b>Binary Cross-Entropy with Logits Loss</b> (<code>BCEWithLogitsLoss</code>) summed across all five heads:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "$$\\mathcal{L} = - \\sum_{i=1}^{5} \\Big[ y_i \\log(\\sigma(z_i)) + (1 - y_i) \\log(1 - \\sigma(z_i)) \\Big]$$",
        styles["BodyBold"]
    ))
    story.append(Paragraph(
        "At inference time, each category's predicted score is $S_i = \\text{round}(\\sigma(z_i) \\times 100)$. A hazard is flagged as positive "
        "if $\\sigma(z_i) \\ge 0.50$ (the default decision threshold).",
        styles["Body"]
    ))

    story.append(Paragraph("2.4 Composite Risk Scoring Formula", styles["H2"]))
    story.append(Paragraph(
        "To prevent a contract with a catastrophic Critical flaw (e.g., <code>selfdestruct</code> score = 95%) from receiving a mild overall score "
        "due to arithmetic averaging across four safe categories (scores = 5%), the application applies a <b>weighted maximum dampener</b> "
        "(<code>backend/analysis/engine.py:853-856</code>):",
        styles["Body"]
    ))
    story.append(Paragraph(
        "$$\\text{Composite Risk Score} = \\min\\Big(100, \\text{round}\\big(0.70 \\times \\max_i(S_i) + 0.30 \\times \\bar{S}\\big)\\Big)$$",
        styles["BodyBold"]
    ))
    story.append(Paragraph(
        "where $\\max_i(S_i)$ is the highest individual category score and $\\bar{S} = \\frac{1}{5}\\sum_{i=1}^5 S_i$ is the arithmetic mean. "
        "The composite score maps to discrete severity tiers: <b>Critical</b> (80–100), <b>High</b> (60–79), <b>Medium</b> (35–59), and <b>Low</b> (0–34).",
        styles["Body"]
    ))

    story.append(Paragraph("2.5 Explainable AI (XAI): SHAP, LIME, and Gradient Saliency", styles["H2"]))
    story.append(Paragraph(
        "Explainability is mandatory in legal informatics because auditors must understand <i>which tokens or clauses induced the model's prediction</i>. "
        "The project implements three genuine mathematical explainability layers:",
        styles["Body"]
    ))
    story.append(Paragraph(
        "1. <b>SHAP (SHapley Additive exPlanations)</b> (<code>backend/analysis/engine.py:359-427</code>): Uses <code>shap.Explainer</code> over "
        "the model's prediction probability function. It computes game-theoretic Shapley values by evaluating marginal probability shifts across "
        "input token coalitions, quantifying how much each token pushed the predicted risk up (positive impact) or down (negative impact).<br/>"
        "2. <b>LIME (Local Interpretable Model-agnostic Explanations)</b> (<code>backend/analysis/engine.py:429-496</code>): Uses "
        "<code>LimeTextExplainer</code>. It perturbs the normalized contract text by masking token subsets, queries Legal-BERT on the perturbed samples, "
        "and fits an interpretable local linear surrogate model weighted by exponential cosine distance. The linear weights indicate local feature importance.<br/>"
        "3. <b>Word Embedding Gradient Saliency (Input $\\times$ Gradient)</b> (<code>backend/analysis/engine.py:298-357</code>): Uses PyTorch autograd "
        "to compute the exact gradient of the target category logit with respect to Legal-BERT's input word embedding layer: "
        "$\\text{Saliency}_j = \\sum_d (w_{jd} \\times \\frac{\\partial z_c}{\\partial w_{jd}})$. This identifies direct neural sensitivity.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: COMPLETE ARCHITECTURE AND DATA FLOW
    # =========================================================================
    story.append(Paragraph("3. Complete Architecture and Data Flow", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("3.1 Architectural Decomposition", styles["H2"]))
    story.append(Paragraph(
        "The application architecture strictly isolates presentation, routing, API orchestration, deep-learning inference, and local persistence. "
        "Figure 1 illustrates the system components, network boundaries, and inter-service communication channels.",
        styles["Body"]
    ))

    # Architecture diagram image
    story.append(Spacer(1, 4))
    story.append(RLImage(arch_png, width=7.2*inch, height=4.4*inch))
    story.append(Paragraph("<b>Figure 1:</b> System Architecture and Component Boundaries across Frontend, FastAPI, Neural Engine, and SQLite Persistence.", styles["MetaBanner"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.2 End-to-End Sequence & Asynchronous Job Flow", styles["H2"]))
    story.append(Paragraph(
        "Figure 2 illustrates the step-by-step lifecycle from the moment a user submits a Solidity contract until results are displayed, "
        "queried via the legal assistant, and exported as executive audit reports.",
        styles["Body"]
    ))

    # Sequence diagram image
    story.append(Spacer(1, 4))
    story.append(RLImage(seq_png, width=7.2*inch, height=4.25*inch))
    story.append(Paragraph("<b>Figure 2:</b> End-to-End Analysis Sequence, Job Stepper Lifecycle, and Report Export Flow.", styles["MetaBanner"]))
    story.append(Spacer(1, 10))

    # Detailed step-by-step narration
    story.append(Paragraph("Detailed Step-by-Step Flow:", styles["H3"]))
    story.append(Paragraph(
        "<b>Step 1: Contract Input:</b> The user opens the frontend at <code>http://127.0.0.1:5173/</code>. In <code>NewAnalysis.jsx</code>, the user pastes raw Solidity code or drops a <code>.sol</code> file. Quick-load buttons allow loading sample contracts.<br/>"
        "<b>Step 2: Frontend Pre-Flight Validation:</b> <code>NewAnalysis.jsx</code> verifies contract name, non-empty code, and checks that payload size is <= 1MB. It probes backend readiness via <code>api.checkHealth()</code>.<br/>"
        "<b>Step 3: Job Submission:</b> The client issues <code>POST /api/v1/analyze/jobs</code> with an idempotency key (or <code>POST /api/v1/analyze/jobs/upload</code> for multipart files). The backend returns HTTP 202 Accepted with a unique <code>jobId</code>.<br/>"
        "<b>Step 4: Background Execution:</b> A background worker thread executes <code>_execute_job_analysis</code>, updating the SQLite <code>jobs</code> table and in-memory tracker across 6 discrete stages: <code>validating</code> ➔ <code>parsing</code> ➔ <code>inferring</code> ➔ <code>attributing</code> ➔ <code>saving</code> ➔ <code>completed</code>.<br/>"
        "<b>Step 5: Client Polling:</b> <code>NewAnalysis.jsx</code> polls <code>GET /api/v1/jobs/{jobId}</code> at 1.2-second intervals, updating the live progress bar and status text.<br/>"
        "<b>Step 6: Completion & Transition:</b> When status reaches <code>completed</code>, the client retrieves the full audit payload and navigates to <code>/analysis/:id</code>.<br/>"
        "<b>Step 7: Result Exploration:</b> <code>AnalysisResult.jsx</code> renders the overall risk score gauge, 5 category risk cards, the interactive <code>CodeViewer</code> with hazard badges, SHAP/LIME charts, and remediation recommendations.<br/>"
        "<b>Step 8: Interactive Assistant & Exports:</b> The user can query <code>LegalChatAssistant</code> (scoped strictly to the contract) and click 'Export PDF' or 'Export DOCX' to download compliance reports dynamically generated by <code>backend/analysis/reports.py</code>.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: FRONTEND WALKTHROUGH
    # =========================================================================
    story.append(Paragraph("4. Frontend Walkthrough", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("4.1 Startup, Routing, and Layout Hierarchy", styles["H2"]))
    story.append(Paragraph(
        "The frontend is built with <b>React 19</b>, <b>Vite 8</b>, <b>Tailwind CSS v4</b>, and <b>React Router v7</b>. "
        "Application entry is in <code>frontend/src/main.jsx</code>, which mounts <code>frontend/src/App.jsx</code> wrapped in "
        "<code>ThemeProvider</code> and <code>AuthProvider</code>.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "In the current local edition, all core analysis features are accessible directly without authentication. "
        "Routes for <code>/login</code>, <code>/register</code>, <code>/profile</code>, and <code>/admin</code> are safely redirected to <code>/dashboard</code>:",
        styles["Body"]
    ))

    code_app_routes = (
        "<Routes>\n"
        "  {/* Public Landing Route */}\n"
        "  <Route element={<PublicLayout />}>\n"
        "    <Route path=\"/\" element={<Landing />} />\n"
        "  </Route>\n\n"
        "  {/* Local Workspace Routes (Direct Access, No Login Required) */}\n"
        "  <Route element={<DashboardLayout />}>\n"
        "    <Route path=\"/dashboard\" element={<Dashboard />} />\n"
        "    <Route path=\"/analysis/new\" element={<NewAnalysis />} />\n"
        "    <Route path=\"/analysis/:id\" element={<AnalysisResult />} />\n"
        "    <Route path=\"/history\" element={<History />} />\n"
        "    <Route path=\"/reports\" element={<Reports />} />\n"
        "    <Route path=\"/settings\" element={<Settings />} />\n"
        "  </Route>\n\n"
        "  {/* Obsolete Auth/Admin routes safely redirected to local dashboard */}\n"
        "  <Route path=\"/login\" element={<Navigate to=\"/dashboard\" replace />} />\n"
        "  <Route path=\"/register\" element={<Navigate to=\"/dashboard\" replace />} />\n"
        "  <Route path=\"/profile\" element={<Navigate to=\"/dashboard\" replace />} />\n"
        "  <Route path=\"/admin\" element={<Navigate to=\"/dashboard\" replace />} />\n"
        "</Routes>"
    )
    story.append(make_code_box(code_app_routes, "frontend/src/App.jsx", "21-45", "App"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.2 Analysis Submission & Polling in NewAnalysis.jsx", styles["H2"]))
    story.append(Paragraph(
        "In <code>frontend/src/pages/NewAnalysis.jsx:228-360</code>, the <code>handleStartAnalysis</code> routine handles contract submission. "
        "It validates input length, checks that the backend is online, generates a unique idempotency key, initiates the job, and starts the polling loop:",
        styles["Body"]
    ))

    code_new_analysis_submit = (
        "const handleStartAnalysis = async (e) => {\n"
        "  e.preventDefault();\n"
        "  if (!contractName.trim() || !solidityCode.trim()) return;\n"
        "  if (backendStatus === 'offline') {\n"
        "    setErrorMessage('Cannot initiate analysis: Backend service is currently unreachable.');\n"
        "    return;\n"
        "  }\n\n"
        "  setIsAnalyzing(true);\n"
        "  const idempotencyKey = `idem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;\n"
        "  const job = await api.createAnalysisJob({\n"
        "    sourceCode: solidityCode, contractName, description, idempotencyKey\n"
        "  });\n"
        "  setActiveJobId(job.jobId);\n\n"
        "  // Poll job status at 1.2s intervals\n"
        "  const poll = async () => {\n"
        "    const statusRes = await api.getJobStatus(job.jobId);\n"
        "    if (statusRes.status === 'completed') {\n"
        "      setIsAnalyzing(false);\n"
        "      const finalResult = statusRes.result || (await api.getJobResult(job.jobId));\n"
        "      navigate(`/analysis/${finalResult.analysisId}`, { state: { analysisResult: finalResult } });\n"
        "    }\n"
        "  };\n"
        "};"
    )
    story.append(make_code_box(code_new_analysis_submit, "frontend/src/pages/NewAnalysis.jsx", "228-337", "handleStartAnalysis"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.3 Results Resolution in AnalysisResult.jsx", styles["H2"]))
    story.append(Paragraph(
        "When <code>AnalysisResult.jsx</code> loads, it resolves data in <code>loadAuditReport</code> via a strict priority hierarchy: "
        "(1) React Router navigation state, (2) live backend query via <code>api.getAnalysis(id)</code>. If the analysis cannot be found, "
        "it displays an explicit error message rather than falling back to fabricated mock data (<code>frontend/src/pages/AnalysisResult.jsx:53-85</code>):",
        styles["Body"]
    ))

    code_analysis_load = (
        "useEffect(() => {\n"
        "  async function loadAuditReport() {\n"
        "    // 1. Check if passed via React Router navigation state\n"
        "    const stateResult = location.state?.analysisResult;\n"
        "    if (stateResult && (stateResult.analysisId === id || stateResult.id === id)) {\n"
        "      setContract(stateResult);\n"
        "      setLoading(false);\n"
        "      return;\n"
        "    }\n"
        "    // 2. Check cached or live API service\n"
        "    try {\n"
        "      const liveResult = await api.getAnalysis(id);\n"
        "      if (liveResult) { setContract(liveResult); setLoading(false); return; }\n"
        "    } catch (err) { console.warn('API lookup by ID failed:', err); }\n"
        "    // 3. Local no-login mode: Do NOT fall back to static mock data\n"
        "    setLoadError(`Audit report '${id}' could not be located in local storage or active session cache.`);\n"
        "    setLoading(false);\n"
        "  }\n"
        "  loadAuditReport();\n"
        "}, [id, location.state]);"
    )
    story.append(make_code_box(code_analysis_load, "frontend/src/pages/AnalysisResult.jsx", "53-86", "loadAuditReport"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.4 Solidity Code Viewer & Line Risk Badges", styles["H2"]))
    story.append(Paragraph(
        "In <code>frontend/src/components/analysis/CodeViewer.jsx</code>, smart-contract lines are split, formatted with non-selectable "
        "gutter line numbers, and dynamically decorated with severity badges based on Legal-BERT findings:",
        styles["Body"]
    ))

    code_viewer_risk = (
        "const getLineRisk = (lineNum) => {\n"
        "  if (hasDynamicFindings) {\n"
        "    const match = findings.find((f) => (f.lineNumbers || []).includes(lineNum));\n"
        "    if (!match) return null;\n"
        "    const badgeClasses = {\n"
        "      Critical: 'bg-red-500/20 text-red-300 border-red-500/30',\n"
        "      High: 'bg-orange-500/20 text-orange-300 border-orange-500/30',\n"
        "      Medium: 'bg-amber-500/20 text-amber-300 border-amber-500/30',\n"
        "      Low: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',\n"
        "    };\n"
        "    return {\n"
        "      level: match.severity || 'Medium',\n"
        "      category: match.category,\n"
        "      clause: match.snippet ? match.snippet.split('\\n')[0] : match.title,\n"
        "      explanation: match.description,\n"
        "      badgeClass: badgeClasses[match.severity] || badgeClasses.Medium,\n"
        "    };\n"
        "  }\n"
        "  return null;\n"
        "};"
    )
    story.append(make_code_box(code_viewer_risk, "frontend/src/components/analysis/CodeViewer.jsx", "28-51", "getLineRisk"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.5 Interactive AI Legal Assistant UI", styles["H2"]))
    story.append(Paragraph(
        "In <code>frontend/src/components/analysis/LegalChatAssistant.jsx:35-77</code>, the chatbot dispatches inquiries to "
        "<code>api.chatWithAssistant(contractId, query)</code>. The response explicitly displays engine transparency badges "
        "('Generative AI (External LLM)' vs. 'Limited Offline Explanation (Deterministic Analysis)') and separates extracted source evidence "
        "from assistant recommendations.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: BACKEND WALKTHROUGH
    # =========================================================================
    story.append(Paragraph("5. Backend Walkthrough", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("5.1 FastAPI Initialization & Security Middleware", styles["H2"]))
    story.append(Paragraph(
        "The backend entry point is <code>backend/main.py</code>. Because the application runs without passwords in local mode, it enforces "
        "strict security middleware (<code>local_security_middleware</code>) to protect the user's host environment from malicious external websites "
        "attempting cross-origin attacks or DNS rebinding against <code>localhost:8000</code>:",
        styles["Body"]
    ))

    code_sec_middleware = (
        "@app.middleware(\"http\")\n"
        "async def local_security_middleware(request: Request, call_next):\n"
        "    # 1. Host header validation to prevent DNS rebinding\n"
        "    raw_host = request.headers.get(\"host\", \"\").split(\":\")[0].strip().lower()\n"
        "    if raw_host and raw_host not in LOCAL_HOSTS and not raw_host.endswith(\".localhost\"):\n"
        "        if raw_host not in allowed_hosts:\n"
        "            return JSONResponse(\n"
        "                status_code=status.HTTP_403_FORBIDDEN,\n"
        "                content={\"code\": \"INVALID_HOST\", \"message\": f\"Host '{raw_host}' is not permitted.\"}\n"
        "            )\n"
        "    # 2. Browser cross-site protection for state-changing requests\n"
        "    if request.method in (\"POST\", \"PUT\", \"DELETE\", \"PATCH\"):\n"
        "        origin = request.headers.get(\"origin\")\n"
        "        sec_fetch_site = request.headers.get(\"sec-fetch-site\")\n"
        "        if origin and not (origin in cors_origins or bool(ALLOWED_LOCAL_ORIGIN_REGEX.match(origin))):\n"
        "            return JSONResponse(\n"
        "                status_code=status.HTTP_403_FORBIDDEN,\n"
        "                content={\"code\": \"CROSS_SITE_REQUEST_BLOCKED\", \"message\": \"Cross-site request blocked.\"}\n"
        "            )\n"
        "    return await call_next(request)"
    )
    story.append(make_code_box(code_sec_middleware, "backend/main.py", "262-300", "local_security_middleware"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.2 Asynchronous Job Lifecycle & Duplicate Protection", styles["H2"]))
    story.append(Paragraph(
        "In <code>backend/main.py:627-695</code>, <code>POST /api/v1/analyze/jobs</code> accepts analysis requests. "
        "It validates the payload, hashes source code (SHA-256) to detect duplicate submissions, verifies idempotency keys, "
        "persists the job into SQLite, and spawns <code>_execute_job_analysis</code> in a background thread under a concurrency semaphore:",
        styles["Body"]
    ))

    code_job_submit = (
        "@app.post(\"/api/v1/analyze/jobs\", status_code=status.HTTP_202_ACCEPTED)\n"
        "async def create_analysis_job(req: AnalysisJobRequest, request: Request, background_tasks: BackgroundTasks):\n"
        "    source_code = _validate_source(req.sourceCode)\n"
        "    user_id = \"usr-local-offline-auditor\"\n"
        "    source_hash = hashlib.sha256(source_code.encode(\"utf-8\")).hexdigest()\n\n"
        "    # Check for existing identical active job\n"
        "    existing_job = db.get_active_job_by_source_hash(user_id, source_hash)\n"
        "    if existing_job:\n"
        "        return {\"jobId\": existing_job[\"jobId\"], \"status\": existing_job[\"status\"], \"isDuplicate\": True}\n\n"
        "    job_id = f\"job-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}\"\n"
        "    job_record = {\"jobId\": job_id, \"userId\": user_id, \"status\": \"queued\", \"progress\": 0, ...}\n"
        "    db.save_job(job_record)\n"
        "    background_tasks.add_task(_execute_job_analysis, job_id, user_id, source_code, req.contractName)\n"
        "    return {\"jobId\": job_id, \"status\": \"queued\", \"progress\": 0}"
    )
    story.append(make_code_box(code_job_submit, "backend/main.py", "627-695", "create_analysis_job"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.3 Legal-BERT Inference and Explainability Engine", styles["H2"]))
    story.append(Paragraph(
        "The core inference routine resides in <code>backend/analysis/engine.py:632-1089</code> (<code>analyze_source</code>). "
        "When model weights exist, it tokenizes the normalized dual-stream representation, executes PyTorch forward inference, "
        "extracts real line numbers from the AST, and calculates SHAP, LIME, and gradient saliency:",
        styles["Body"]
    ))

    code_engine_inference = (
        "# 4. Neural Inference (When Model Artifact Exists)\n"
        "import torch\n"
        "model, tokenizer = self.get_model_and_tokenizer(self.model_dir)\n"
        "inputs = tokenizer(model_input_text, max_length=512, truncation=True, padding=\"max_length\", return_tensors=\"pt\")\n\n"
        "with torch.no_grad():\n"
        "    outputs = model(**inputs)\n"
        "    logits = outputs.logits.squeeze(0).cpu().numpy()\n"
        "    probabilities = 1.0 / (1.0 + np.exp(-logits))  # 5 independent sigmoid heads\n\n"
        "# 5. Compute Genuine SHAP, LIME, and PyTorch Embedding Gradient Saliency\n"
        "shap_values = compute_genuine_shap(model, tokenizer, model_input_text, target_category_idx=top_category_idx)\n"
        "lime_explanations = compute_genuine_lime(model, tokenizer, model_input_text, target_category_idx=top_category_idx)\n"
        "token_attributions = compute_embedding_gradient_saliency(model, tokenizer, model_input_text, target_category_idx=top_category_idx)\n\n"
        "# Composite Risk Calculation (Weighted Maximum Dampener)\n"
        "composite_score = int(min(100, round((max(risk_breakdown.values()) * 0.7) + (avg_cat_score * 0.3))))"
    )
    story.append(make_code_box(code_engine_inference, "backend/analysis/engine.py", "722-856", "analyze_source"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.4 SQLite Persistence & Reboot Reconciliation", styles["H2"]))
    story.append(Paragraph(
        "Database logic in <code>backend/analysis/db.py</code> manages relational tables (<code>analyses</code>, <code>jobs</code>, <code>stored_files</code>, "
        "<code>users</code>, <code>revoked_tokens</code>, <code>audit_logs</code>). A critical reliability feature is <b>Startup Reboot Reconciliation</b> "
        "(<code>reconcile_interrupted_jobs</code>, lines 340-380): if the backend is abruptly restarted during model inference, in-flight jobs "
        "left in <code>running</code> or <code>queued</code> state are automatically marked <code>failed</code> with stage <code>interrupted</code>, "
        "preventing the client UI from hanging indefinitely on stale jobs.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6: DATASET AND MODEL LIFECYCLE
    # =========================================================================
    story.append(Paragraph("6. Dataset and Model Lifecycle", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("6.1 Canonical Dataset Composition (v3.3.0 Frozen Cycle)", styles["H2"]))
    story.append(Paragraph(
        "The machine-learning dataset is located at <code>data/ml_candidates/final_dataset.jsonl</code>. The file SHA-256 hash is "
        "<code>74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456</code>. It contains 72 records across 32 project families. "
        "Deterministic project-level group isolation (<code>GroupShuffleSplit</code>, <code>seed=42</code>) ensures <b>0.0% cross-split leakage</b>. "
        "Synthetic records are restricted strictly to training; validation and test splits contain 100% real-source contracts:",
        styles["Body"]
    ))

    # Dataset breakdown table
    ds_table_data = [
        [
            Paragraph("<b>Split</b>", styles["TableHead"]),
            Paragraph("<b>Total Records</b>", styles["TableHead"]),
            Paragraph("<b>Real-Source</b>", styles["TableHead"]),
            Paragraph("<b>Synthetic</b>", styles["TableHead"]),
            Paragraph("<b>Project Isolation Families</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Train", styles["TableCellBold"]),
            Paragraph("44 records", styles["TableCell"]),
            Paragraph("24 records (54.5%)", styles["TableCell"]),
            Paragraph("20 records (45.5%)", styles["TableCell"]),
            Paragraph("19 distinct project families", styles["TableCell"]),
        ],
        [
            Paragraph("Validation", styles["TableCellBold"]),
            Paragraph("7 records", styles["TableCell"]),
            Paragraph("7 records (100.0%)", styles["TableCell"]),
            Paragraph("0 records (0.0%)", styles["TableCell"]),
            Paragraph("4 projects (<code>coinbase_base_bridge</code>, <code>spectral_image_vaults</code>, etc.)", styles["TableCell"]),
        ],
        [
            Paragraph("Test (Held-Out)", styles["TableCellBold"]),
            Paragraph("7 records", styles["TableCell"]),
            Paragraph("7 records (100.0%)", styles["TableCell"]),
            Paragraph("0 records (0.0%)", styles["TableCell"]),
            Paragraph("4 projects (<code>anvil_protocol</code>, <code>aragon_vault</code>, <code>virtuals_genesis</code>, etc.)", styles["TableCell"]),
        ],
        [
            Paragraph("Excluded / Unassigned", styles["TableCellBold"]),
            Paragraph("14 records", styles["TableCell"]),
            Paragraph("14 records (100.0%)", styles["TableCell"]),
            Paragraph("0 records", styles["TableCell"]),
            Paragraph("Excluded: 7 license restrictions (6 BUSL-1.1, 1 AGPL-3.0) + 7 extraction defects", styles["TableCell"]),
        ],
    ]
    t_ds = Table(ds_table_data, colWidths=[90, 80, 110, 80, 180])
    t_ds.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ds)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.2 Training Configuration & Execution", styles["H2"]))
    story.append(Paragraph(
        "The training script is <code>analysis/train_legal_bert.py</code> with configuration defined in <code>analysis/training_config.json</code>: "
        "base model = <code>nlpaueb/legal-bert-base-uncased</code>, learning rate = $3 \\times 10^{-5}$ (AdamW optimizer, weight decay = 0.01), "
        "batch size = 4, epochs = 3, linear warmup = 10%, max sequence length = 512. Total training loss declined smoothly across epochs: "
        "Epoch 1 Loss = <code>0.5764</code>, Epoch 2 Loss = <code>0.4358</code>, Epoch 3 Loss = <code>0.3945</code> (~3,000 CPU-seconds).",
        styles["Body"]
    ))

    story.append(Paragraph("6.3 Empirical Benchmark Results on Untouched Held-Out Test Split (N=7)", styles["H2"]))
    story.append(Paragraph(
        "As rigorously documented in <code>docs/LEGAL_BERT_EXPERIMENT_REPORT.md</code>, both the fine-tuned Legal-BERT classifier and a deterministic "
        "TF-IDF + Logistic Regression baseline were evaluated on the exact same untouched held-out real-source test split ($N=7$, 35 binary decisions total):",
        styles["Body"]
    ))

    # Metrics comparison table
    metrics_table_data = [
        [
            Paragraph("<b>Category</b>", styles["TableHead"]),
            Paragraph("<b>Test Pos / Neg</b>", styles["TableHead"]),
            Paragraph("<b>Legal-BERT (Thresh 0.50)</b><br/>TP / FP / FN / TN / F1", styles["TableHead"]),
            Paragraph("<b>TF-IDF Baseline</b><br/>TP / FP / FN / TN / F1", styles["TableHead"]),
            Paragraph("<b>Support & Evaluation Status</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Privacy", styles["TableCellBold"]),
            Paragraph("0 Pos / 7 Neg", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("<b>Inconclusive</b>: Zero positive test support", styles["TableCell"]),
        ],
        [
            Paragraph("Termination", styles["TableCellBold"]),
            Paragraph("3 Pos / 4 Neg", styles["TableCell"]),
            Paragraph("0 / 0 / 3 / 4 (F1: 0.00)", styles["TableCell"]),
            Paragraph("2 / 0 / 1 / 4 (<b>F1: 0.80</b>)", styles["TableCell"]),
            Paragraph("<b>Evaluable</b>: N=3 positives. Baseline detected 2/3.", styles["TableCell"]),
        ],
        [
            Paragraph("Legal Compliance", styles["TableCellBold"]),
            Paragraph("4 Pos / 3 Neg", styles["TableCell"]),
            Paragraph("0 / 0 / 4 / 3 (F1: 0.00)", styles["TableCell"]),
            Paragraph("0 / 0 / 4 / 3 (F1: 0.00)", styles["TableCell"]),
            Paragraph("<b>Evaluable</b>: N=4 positives. Missed at 0.50.", styles["TableCell"]),
        ],
        [
            Paragraph("Liability", styles["TableCellBold"]),
            Paragraph("0 Pos / 7 Neg", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("<b>Inconclusive</b>: Zero positive test support", styles["TableCell"]),
        ],
        [
            Paragraph("Payment / Financial", styles["TableCellBold"]),
            Paragraph("0 Pos / 7 Neg", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("0 / 0 / 0 / 7 (F1: 0.00)", styles["TableCell"]),
            Paragraph("<b>Inconclusive</b>: Zero positive test support", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Global Summary</b>", styles["TableCellBold"]),
            Paragraph("<b>7 Pos / 28 Neg</b>", styles["TableCellBold"]),
            Paragraph("<b>Macro F1: 0.0000</b><br/>Spec: 100.0% | Ham: 0.20", styles["TableCellBold"]),
            Paragraph("<b>Macro F1: 0.1600</b><br/>Spec: 100.0% | Ham: 0.14", styles["TableCellBold"]),
            Paragraph("Evaluable Macro F1: Baseline = 0.4000, Legal-BERT = 0.0000", styles["TableCellBold"]),
        ],
    ]
    t_metrics = Table(metrics_table_data, colWidths=[90, 80, 120, 110, 140])
    t_metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.4 Honest Disclosure of Small-Data Boundaries & Zero Human Claims", styles["H2"]))
    story.append(Paragraph(
        "In strict adherence to empirical academic standards, the project reports the following necessary limitations:<br/>"
        "1. <b>Zero Human-Verified Claims</b>: 100% of canonical records have <code>human_verified: false</code> and <code>review_status: 'ai_reviewed'</code>. "
        "Labels reflect careful AI-assisted operational categorization, not legal opinions from human attorneys.<br/>"
        "2. <b>Threshold Calibration Constraint</b>: The validation split contained 0 positive examples. In statistical modeling, threshold calibration "
        "on an all-negative distribution collapses thresholds toward zero, causing degenerate overfitting. All five heads were thus responsibly kept at "
        "the default uncalibrated threshold of <code>0.50</code>.<br/>"
        "3. <b>Zero-Support Categories</b>: In the held-out test split ($N=7$), Privacy, Liability, and Payment/Financial had zero ground-truth positive "
        "examples. The 0.0000 F1 score reflects the mathematical impossibility of computing recall without positive ground truth, not necessarily "
        "a total absence of model capacity.<br/>"
        "4. <b>Negative Prediction Conservatism</b>: The neural classifier achieved <b>100.0% Specificity</b> (correctly classifying 28 out of 28 negative "
        "labels with 0 false positives). However, predicted probabilities ranged between 0.18 and 0.26, failing to cross the uncalibrated 0.50 threshold "
        "for the positive test cases in Termination and Legal Compliance.",
        styles["Body"]
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 7: INSTALLATION, EXECUTION, AND TESTING
    # =========================================================================
    story.append(Paragraph("7. Installation, Execution, and Testing", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("7.1 Prerequisites & System Requirements", styles["H2"]))
    story.append(Paragraph(
        "The project requires Python 3.10+ (tested on Python 3.14.3), Node.js 18+ (tested on Node 20+), npm 9+, Git, and ~1.5 GB of free disk space "
        "(model checkpoint = 438 MB, node_modules = ~200 MB, PyTorch virtualenv = ~800 MB).",
        styles["Body"]
    ))

    story.append(Paragraph("7.2 Setup and Launch Commands", styles["H2"]))
    story.append(Paragraph(
        "<b>Terminal 1 — Backend & Model Setup:</b>", styles["BodyBold"]
    ))
    backend_cmds = (
        "# 1. Setup virtual environment\n"
        "python -m venv .venv\n"
        ".venv\\Scripts\\Activate.ps1    # On Linux/macOS: source .venv/bin/activate\n\n"
        "# 2. Install dependencies\n"
        "python -m pip install --upgrade pip\n"
        "pip install -r requirements.txt\n\n"
        "# 3. Download & verify Legal-BERT v3.3.0 model weights (438 MB)\n"
        "python scripts/setup_model.py\n"
        "# To check hash only: python scripts/setup_model.py --check-only\n\n"
        "# 4. Launch FastAPI server on loopback\n"
        "uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
    )
    story.append(make_code_box(backend_cmds, "Terminal 1 (Backend)", "Setup Steps", "PowerShell/Bash"))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>Terminal 2 — Frontend Setup & Launch:</b>", styles["BodyBold"]
    ))
    frontend_cmds = (
        "cd frontend\n"
        "npm install\n"
        "npm run dev\n"
        "# Open browser at http://localhost:5173/ (or http://127.0.0.1:5173/)"
    )
    story.append(make_code_box(frontend_cmds, "Terminal 2 (Frontend)", "Setup Steps", "Bash/PowerShell"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("7.3 Automated Test Suite Execution & Truthful Verification Results", styles["H2"]))
    story.append(Paragraph(
        "During this documentation inspection, the complete automated test suite was executed against the active repository code. "
        "The results are recorded truthfully below:",
        styles["Body"]
    ))

    test_table_data = [
        [
            Paragraph("<b>Test Suite Module</b>", styles["TableHead"]),
            Paragraph("<b>Target Scope & Verification Focus</b>", styles["TableHead"]),
            Paragraph("<b>Tests</b>", styles["TableHead"]),
            Paragraph("<b>Outcome</b>", styles["TableHead"]),
        ],
        [
            Paragraph("<code>tests/test_api.py</code>", styles["TableCellCode"]),
            Paragraph("API schema validation, HTTP error codes (400, 413, 422), headers, endpoints", styles["TableCell"]),
            Paragraph("22", styles["TableCell"]),
            Paragraph("<b>22 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_auth.py</code>", styles["TableCellCode"]),
            Paragraph("Local user bypass, registration, bcrypt password hashing, token revocation", styles["TableCell"]),
            Paragraph("9", styles["TableCell"]),
            Paragraph("<b>9 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_end_to_end_workflow.py</code>", styles["TableCellCode"]),
            Paragraph("End-to-end integration: submission ➔ inference ➔ result retrieval", styles["TableCell"]),
            Paragraph("1", styles["TableCell"]),
            Paragraph("<b>1 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_jobs_assistant_reports.py</code>", styles["TableCellCode"]),
            Paragraph("Job async lifecycle, idempotency, cancellation (410), reboot reconcile, chat, PDF/DOCX", styles["TableCell"]),
            Paragraph("10", styles["TableCell"]),
            Paragraph("<b>10 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_legacy_benchmark_rules.py</code>", styles["TableCellCode"]),
            Paragraph("Legacy benchmark rule engine complete isolation from active inference", styles["TableCell"]),
            Paragraph("1", styles["TableCell"]),
            Paragraph("<b>1 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_ml_dataset_validator.py</code>", styles["TableCellCode"]),
            Paragraph("Dataset schema validation, split isolation, provenance, license checks", styles["TableCell"]),
            Paragraph("18", styles["TableCell"]),
            Paragraph("<b>18 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_ownership.py</code>", styles["TableCellCode"]),
            Paragraph("Data ownership, user history isolation, unauthenticated access in local mode", styles["TableCell"]),
            Paragraph("11", styles["TableCell"]),
            Paragraph("<b>11 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<code>tests/test_storage_lifecycle.py</code>", styles["TableCellCode"]),
            Paragraph("File upload validation, path traversal defense, 30-day retention cleanup", styles["TableCell"]),
            Paragraph("15", styles["TableCell"]),
            Paragraph("<b>15 PASSED</b>", styles["BadgeMatches"]),
        ],
        [
            Paragraph("<b>TOTAL TEST SUITE</b>", styles["TableCellBold"]),
            Paragraph("<b>Full automated backend verification (Python 3.14.3 / Pytest 9.1.1)</b>", styles["TableCellBold"]),
            Paragraph("<b>87</b>", styles["TableCellBold"]),
            Paragraph("<b>87 PASSED (0 failures, 529s)</b>", styles["BadgeMatches"]),
        ],
    ]
    t_tests = Table(test_table_data, colWidths=[140, 240, 45, 115])
    t_tests.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_tests)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 8: DOCUMENTATION-VERSUS-CODE COMPARISON
    # =========================================================================
    story.append(Paragraph("8. Documentation-versus-Code Comparison", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph(
        "This critical section directly compares the authoritative project specification "
        "(<code>docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx</code>) and earlier documentation drafts "
        "(e.g., <code>docs/CURRENT_STATE_AND_GAPS.md</code>) against the actual code implementation. "
        "Discrepancies and necessary documentation corrections are explicitly highlighted:",
        styles["Body"]
    ))

    comparison_data = [
        [
            Paragraph("<b>Feature or Claim</b>", styles["TableHead"]),
            Paragraph("<b>Specification / Earlier Doc Statement</b>", styles["TableHead"]),
            Paragraph("<b>Actual Code Implementation</b>", styles["TableHead"]),
            Paragraph("<b>Status</b>", styles["TableHead"]),
            Paragraph("<b>Verified Evidence</b>", styles["TableHead"]),
            Paragraph("<b>Recommended Doc Correction</b>", styles["TableHead"]),
        ],
        [
            Paragraph("User Authentication & Accounts", styles["TableCellBold"]),
            Paragraph("Spec Phase 1/2: Email & password login, Google/GitHub OAuth, email verification.", styles["TableCell"]),
            Paragraph("<b>Zero Login Required</b> in current release. Routes <code>/login</code>, <code>/register</code>, <code>/profile</code> redirect to <code>/dashboard</code>.", styles["TableCell"]),
            Paragraph("Differs", styles["BadgeDiffers"]),
            Paragraph("<code>frontend/src/App.jsx:37-42</code>;<br/><code>backend/main.py:408-424</code>", styles["TableCellCode"]),
            Paragraph("Update specification to clarify that Milestone 1/local release intentionally bypasses login for single-user offline college evaluation.", styles["TableCell"]),
        ],
        [
            Paragraph("Deep Learning Model Implementation", styles["TableCellBold"]),
            Paragraph("Earlier draft (<code>CURRENT_STATE_AND_GAPS.md</code>): Claimed 'no backend, no model weights, simulated setInterval in frontend'.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. Canonical backend loads fine-tuned Legal-BERT v3.3.0 (438MB SafeTensors), performs genuine PyTorch neural inference.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/analysis/engine.py:498-550</code>;<br/><code>backend/main.py:36</code>", styles["TableCellCode"]),
            Paragraph("Mark gap audit in <code>CURRENT_STATE_AND_GAPS.md</code> as superseded by the completed Legal-BERT v3.3.0 implementation.", styles["TableCell"]),
        ],
        [
            Paragraph("Asynchronous Analysis & Job Stepper", styles["TableCellBold"]),
            Paragraph("Spec Phase 4: Async backend pipeline with real-time loading screen showing stage and progress %.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. <code>POST /api/v1/analyze/jobs</code> creates SQLite job; worker thread tracks 6 stages; client polls <code>/jobs/{id}</code>.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/main.py:426-538, 627-695</code>;<br/><code>frontend/src/pages/NewAnalysis.jsx:271-337</code>", styles["TableCellCode"]),
            Paragraph("None. Documentation and implementation match perfectly.", styles["TableCell"]),
        ],
        [
            Paragraph("Explainable AI (SHAP & LIME)", styles["TableCellBold"]),
            Paragraph("Spec Phase 4/5: SHAP game-theoretic values and LIME local feature interpretability.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. Genuine mathematical SHAP (<code>shap.Explainer</code>) and LIME (<code>LimeTextExplainer</code>) plus PyTorch autograd gradient saliency.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/analysis/engine.py:298-496</code>;<br/><code>frontend/src/components/analysis/ShapChart.jsx</code>", styles["TableCellCode"]),
            Paragraph("Document that PyTorch word-embedding gradient saliency was added alongside SHAP and LIME for deeper token sensitivity.", styles["TableCell"]),
        ],
        [
            Paragraph("Context-Scoped Legal Assistant", styles["TableCellBold"]),
            Paragraph("Spec Phase 6: Conversational chatbot strictly scoped to analyzed contract clauses.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. <code>backend/analysis/chat.py</code> evaluates queries solely against contract AST and findings. Supports optional LLM with offline fallback.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/analysis/chat.py:45-195</code>;<br/><code>frontend/src/components/analysis/LegalChatAssistant.jsx</code>", styles["TableCellCode"]),
            Paragraph("Clarify that assistant operates with limited deterministic rule-based explanations when no external OpenAI API key is supplied.", styles["TableCell"]),
        ],
        [
            Paragraph("Audit Report Generation", styles["TableCellBold"]),
            Paragraph("Spec Phase 7: Export professional executive audit reports in PDF and editable DOCX formats.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. <code>backend/analysis/reports.py</code> uses ReportLab and python-docx to generate dynamic reports with XAI attributions.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/analysis/reports.py:28-428</code>;<br/><code>backend/main.py:1040-1105</code>", styles["TableCellCode"]),
            Paragraph("None. Fully operational and verified by automated test suite.", styles["TableCell"]),
        ],
        [
            Paragraph("Data Retention & Cleanup", styles["TableCellBold"]),
            Paragraph("Spec / Docs: Ephemeral in-memory store vs. permanent database storage policy.", styles["TableCell"]),
            Paragraph("<b>Hybrid Architecture</b>. In-memory LRU store (100 entries, 30m TTL) for fast tab switching + SQLite DB with 30-day retention and background cleanup worker.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/main.py:78-82, 198-212</code>;<br/><code>backend/analysis/db.py:450-520</code>", styles["TableCellCode"]),
            Paragraph("Clarify in architecture guide that both in-memory caching and local SQLite persistence are operational.", styles["TableCell"]),
        ],
        [
            Paragraph("Admin Control Panel", styles["TableCellBold"]),
            Paragraph("Spec Phase 13: User management, model weight deployment, resource monitoring, audit logs.", styles["TableCell"]),
            Paragraph("<b>Partial</b>. Backend endpoints exist (<code>/api/v1/admin/...</code>), but UI route <code>/admin</code> redirects to <code>/dashboard</code> in current single-user release.", styles["TableCell"]),
            Paragraph("Partial", styles["BadgePartial"]),
            Paragraph("<code>frontend/src/App.jsx:41</code>;<br/><code>backend/main.py:1180-1250</code>", styles["TableCellCode"]),
            Paragraph("Label Admin Dashboard as 'Enterprise Phase / Multi-User Roadmap' in user-facing documentation.", styles["TableCell"]),
        ],
        [
            Paragraph("Job Cancellation & Reconcile", styles["TableCellBold"]),
            Paragraph("Spec / Architecture: Ability to cancel in-flight jobs and recover from server restarts.", styles["TableCell"]),
            Paragraph("<b>Fully Implemented</b>. <code>POST /api/v1/jobs/{id}/cancel</code> cancels job (returns 410 Gone on result); <code>reconcile_interrupted_jobs()</code> recovers on startup.", styles["TableCell"]),
            Paragraph("Matches", styles["BadgeMatches"]),
            Paragraph("<code>backend/main.py:820-858</code>;<br/><code>backend/analysis/db.py:340-380</code>", styles["TableCellCode"]),
            Paragraph("Add reboot reconciliation behavior to system operations manual.", styles["TableCell"]),
        ],
    ]
    t_comp = Table(comparison_data, colWidths=[80, 100, 120, 45, 95, 100])
    t_comp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 9: FINAL LIMITATIONS AND CONCLUSION
    # =========================================================================
    story.append(Paragraph("9. Final Limitations and Conclusion", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=1, spaceAfter=8))

    story.append(Paragraph("9.1 Current Implementation Summary", styles["H2"]))
    story.append(Paragraph(
        "The current, finalized version of <b>Smart_Contract_Analyser</b> represents a fully functioning, locally private, and rigorous "
        "research prototype. The core frontend, FastAPI server, asynchronous job lifecycle, Legal-BERT v3.3.0 neural classifier, genuine SHAP "
        "and LIME explainers, context-grounded legal assistant, local SQLite persistence, and executive PDF/DOCX report exporters are all "
        "fully implemented, verified, and backed by 87 passing automated tests.",
        styles["Body"]
    ))

    story.append(Paragraph("9.2 Partially Implemented & Deferred Capabilities", styles["H2"]))
    story.append(Paragraph(
        "To maintain transparency during academic review, the following components are acknowledged as deferred or partially implemented:<br/>"
        "• <b>Admin Control Panel & User RBAC</b>: Backend admin and user-management endpoints exist in code, but the frontend interface "
        "is currently redirected to <code>/dashboard</code> because the active release is optimized for single-user local evaluation.<br/>"
        "• <b>Non-Solidity Smart Contracts</b>: The parser and model currently target Solidity (<code>.sol</code>). Support for Vyper, Move, "
        "and Rust (Solana/Near) remains on the future enterprise roadmap.<br/>"
        "• <b>Legal PDF Contract Ingestion</b>: The upload workspace accepts Solidity source files; uploading natural-language PDF commercial "
        "contracts for cross-comparison with code is a roadmap item.",
        styles["Body"]
    ))

    story.append(Paragraph("9.3 Responsible Presentation of AI and Model Claims", styles["H2"]))
    story.append(Paragraph(
        "When presenting this project in academic or demonstration contexts, the following claims must be presented with precision:<br/>"
        "1. <b>Decision-Support, Not Legal Advice</b>: The application flags operational risk indicators; it does not issue formal legal opinions "
        "or guarantee statutory enforceability.<br/>"
        "2. <b>Training Data Boundaries</b>: The model was trained on 44 records (24 real-source, 20 synthetic) and evaluated on 7 untouched real-source "
        "contracts. 100% of annotations are <code>ai_reviewed</code>; zero human-verified claims are made.<br/>"
        "3. <b>Zero-Support Categories</b>: For Privacy, Liability, and Payment/Financial, test recall is mathematically non-evaluable on the held-out "
        "split due to zero positive ground truth. Termination and Legal Compliance are evaluable, but positives were missed at threshold 0.50.<br/>"
        "4. <b>Negative Finding Safety Warning</b>: A low risk score or an absence of flagged findings does <b>NOT</b> prove that a contract is safe "
        "or compliant. Always perform independent professional legal and security audits.",
        styles["Body"]
    ))

    story.append(Paragraph("9.4 Setup and Portability Considerations for Collaborators", styles["H2"]))
    story.append(Paragraph(
        "When sharing or cloning the project across different environments (Windows, macOS, Linux):<br/>"
        "• <b>Model Weight Acquisition</b>: Because <code>model.safetensors</code> is 438 MB, it is not committed directly to Git. Collaborators "
        "must run <code>python scripts/setup_model.py</code> to automatically download and verify the release weights.<br/>"
        "• <b>Python Path Configuration</b>: When running pytest or custom scripts, ensure the repository root is on <code>sys.path</code> "
        "(e.g., run <code>python -m pytest</code> rather than standalone <code>pytest</code>).<br/>"
        "• <b>Loopback Ports</b>: Ensure local ports <code>8000</code> (FastAPI) and <code>5173</code> (Vite) are available and not blocked by local firewalls.",
        styles["Body"]
    ))
    story.append(Spacer(1, 14))

    # Concluding signature box
    sig_data = [
        [
            Paragraph(
                "<b>Document Title:</b> Smart Contract Analyser — Complete Theory & Code Walkthrough<br/>"
                "<b>Verification Status:</b> 100% Code-Verified against Active Repository & Git Branch <code>main</code><br/>"
                "<b>Test Suite Verification:</b> 87 passed in 529.62s (Python 3.14.3 / Pytest 9.1.1)<br/>"
                "<b>Final Output Document:</b> <code>docs/PROJECT_THEORY_AND_CODE_WALKTHROUGH.pdf</code>",
                styles["MetaBanner"]
            )
        ]
    ]
    t_sig = Table(sig_data, colWidths=[letter[0] - 72])
    t_sig.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#94a3b8")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sig)

    print("[3/4] Building PDF with NumberedCanvas...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[4/4] Successfully generated PDF: {output_filename}")

    # Clean up temporary diagram images
    for p in [arch_png, seq_png]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


if __name__ == "__main__":
    out_pdf = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "PROJECT_THEORY_AND_CODE_WALKTHROUGH.pdf"
    )
    build_pdf(out_pdf)
