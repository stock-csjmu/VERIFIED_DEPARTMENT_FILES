from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
import pandas as pd
from datetime import datetime
import re
import html


def generate_pdf_report(department_name, df):
    """
    Simple, Excel-style departmental inventory verification report.

    Layout:
      Page 1  : Department details + verification abstract
      Next    : AVAILABLE / FOUND items - complete list in tabular form
      Next    : Other verification statuses, each in its own table
      Final   : Declaration + HOD / committee signatures

    Existing Streamlit function signature is preserved.
    """

    df = df.copy()

    # ---------------------------------------------------------
    # Expected columns - missing columns are safely blank.
    # ---------------------------------------------------------
    columns = [
        "Reference No.", "Name of the Item", "Inventory Category",
        "Inventory Sub Category", "Bill Number", "Bill Date",
        "Total Quantity", "Available Quantity",
        "Verified Available Quantity", "Missing Quantity",
        "Verification Status", "Condition", "Building", "Floor",
        "Room No", "Cabin/Lab/Classroom", "Exact Physical Location",
        "Custodian/User", "Remarks", "Observation",
        "Department Observation", "Verification Remarks",
        "Verified By", "Verification Date"
    ]

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    def val(x):
        if pd.isna(x):
            return ""
        return str(x).strip()

    def num(x):
        try:
            if pd.isna(x) or val(x) == "":
                return None
            return float(x)
        except Exception:
            return None

    def qty(x):
        n = num(x)
        if n is None:
            return ""
        return str(int(n)) if n.is_integer() else f"{n:g}"

    def clean(x):
        return re.sub(r"\s+", " ", val(x)).strip()

    def safe(x):
        return html.escape(val(x), quote=False)

    def P(x, style="cell"):
        return Paragraph(safe(x), styles[style])

    # ---------------------------------------------------------
    # Normalize quantities.
    # ---------------------------------------------------------
    for col in [
        "Total Quantity", "Available Quantity",
        "Verified Available Quantity", "Missing Quantity"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---------------------------------------------------------
    # Derive status without converting Pending into Missing.
    # Existing explicit status is respected.
    # ---------------------------------------------------------
    statuses = []

    for _, r in df.iterrows():
        source = clean(r["Verification Status"]).upper()
        condition = clean(r["Condition"]).upper()

        observation_parts = []
        for c in [
            "Remarks", "Observation", "Department Observation",
            "Verification Remarks"
        ]:
            if c in r.index and clean(r[c]):
                observation_parts.append(clean(r[c]).upper())

        combined = " ".join(
            [source, condition] + observation_parts
        )

        if "WEED OUT" in combined or "WEED-OUT" in combined:
            status = "SCRAP / WEED-OUT"
        elif "SCRAP" in combined:
            status = "SCRAP"
        elif "NOT RECEIVED" in combined:
            status = "NOT RECEIVED / RECORD DISCREPANCY"
        elif "RECORD DISCREPANCY" in combined:
            status = "NOT RECEIVED / RECORD DISCREPANCY"
        elif "PENDING" in combined:
            status = "PENDING VERIFICATION"
        elif "PARTIALLY FOUND" in combined or "PARTIAL" in combined:
            status = "PARTIALLY FOUND"
        elif "MISSING" in combined or "NOT FOUND" in combined:
            status = "MISSING / NOT FOUND"
        elif source in ["FOUND", "AVAILABLE", "FULLY FOUND"]:
            status = "FOUND / AVAILABLE"
        else:
            available = num(r["Available Quantity"])
            if available is None:
                available = num(r["Total Quantity"])
            verified = num(r["Verified Available Quantity"])

            if verified is None:
                status = "PENDING VERIFICATION"
            elif available is not None and verified >= available:
                status = "FOUND / AVAILABLE"
            elif verified > 0:
                status = "PARTIALLY FOUND"
            else:
                status = "MISSING / NOT FOUND"

        statuses.append(status)

    df["_Report Status"] = statuses

    # Missing quantity: use source value if present, otherwise calculate
    # only for completed verification statuses.
    missing = []
    for _, r in df.iterrows():
        source_missing = num(r["Missing Quantity"])
        if source_missing is not None:
            missing.append(max(source_missing, 0))
            continue

        available = num(r["Available Quantity"])
        if available is None:
            available = num(r["Total Quantity"])
        verified = num(r["Verified Available Quantity"])

        if (
            r["_Report Status"] in
            ["FOUND / AVAILABLE", "PARTIALLY FOUND", "MISSING / NOT FOUND"]
            and available is not None
            and verified is not None
        ):
            missing.append(max(available - verified, 0))
        else:
            missing.append(0)

    df["_Report Missing"] = missing

    # ---------------------------------------------------------
    # Report calculations.
    # ---------------------------------------------------------
    total_records = len(df)
    total_recorded = int(df["Total Quantity"].fillna(0).sum())
    total_available = int(df["Available Quantity"].fillna(
        df["Total Quantity"]).fillna(0).sum())
    total_verified = int(df["Verified Available Quantity"].fillna(0).sum())
    total_missing = int(df["_Report Missing"].sum())

    found = df[df["_Report Status"] == "FOUND / AVAILABLE"]
    partial = df[df["_Report Status"] == "PARTIALLY FOUND"]
    missing_df = df[df["_Report Status"] == "MISSING / NOT FOUND"]
    not_received = df[
        df["_Report Status"] == "NOT RECEIVED / RECORD DISCREPANCY"
    ]
    scrap = df[df["_Report Status"].isin(["SCRAP", "SCRAP / WEED-OUT"])]
    pending = df[df["_Report Status"] == "PENDING VERIFICATION"]

    # ---------------------------------------------------------
    # File.
    # ---------------------------------------------------------
    safe_name = re.sub(r'[<>:"/\\|?*]+', "_", val(department_name))
    safe_name = safe_name.strip() or "Department"

    pdf_file = f"{safe_name}_Verification_Report.pdf"

    # Landscape is deliberate: it allows an Excel-like verification table.
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=landscape(A4),
        leftMargin=6 * mm,
        rightMargin=6 * mm,
        topMargin=10 * mm,
        bottomMargin=11 * mm,
        title=f"{department_name} - Inventory Verification Report",
        author="CSJMU Inventory Verification System"
    )

    # ---------------------------------------------------------
    # Styles.
    # ---------------------------------------------------------
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="University",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=17,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name="ReportHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=3,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=5.8,
        leading=6.7
    ))

    styles.add(ParagraphStyle(
        name="cell_center",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=5.8,
        leading=6.7,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name="small",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9
    ))

    # ---------------------------------------------------------
    # Header/footer.
    # ---------------------------------------------------------
    report_date = datetime.now().strftime("%d/%m/%Y")

    def footer(canvas, document):
        canvas.saveState()
        w, h = landscape(A4)

        canvas.setStrokeColor(colors.HexColor("#AAAAAA"))
        canvas.line(8 * mm, 8 * mm, w - 8 * mm, 8 * mm)

        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(
            8 * mm, 4.5 * mm,
            f"CSJMU | {val(department_name)} | Physical Inventory Verification"
        )
        canvas.drawRightString(
            w - 8 * mm, 4.5 * mm,
            f"Page {document.page}"
        )
        canvas.restoreState()

    story = []

    # =========================================================
    # PAGE 1 - ABSTRACT
    # =========================================================
    story.append(Paragraph(
        "CHHATRAPATI SHAHU JI MAHARAJ UNIVERSITY",
        styles["University"]
    ))
    story.append(Paragraph(
        f"{safe(department_name).upper()}<br/>"
        "PHYSICAL STOCK / INVENTORY VERIFICATION REPORT",
        styles["ReportHeading"]
    ))

    details = [
        [P("Department", "small"), P(department_name, "small"),
         P("Verification / Report Date", "small"), P(report_date, "small")],
        [P("Total Inventory Records", "small"),
         P(total_records, "small"),
         P("Total Available Quantity", "small"),
         P(total_available, "small")],
        [P("Verified Available Quantity", "small"),
         P(total_verified, "small"),
         P("Overall Missing Quantity", "small"),
         P(total_missing, "small")],
        [P("Overall Result", "small"),
         P(
             "VERIFIED WITH DISCREPANCIES"
             if total_missing > 0
             else "VERIFICATION COMPLETED",
             "small"
         ),
         P("Verification Coverage", "small"),
         P(
             f"{total_verified} of {total_available} available quantity verified"
             if total_available
             else "Not available",
             "small"
         )]
    ]

    details_table = Table(
        details,
        colWidths=[42*mm, 70*mm, 48*mm, 110*mm]
    )
    details_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#777777")),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EAF2F8")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#EAF2F8")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4)
    ]))
    story.append(details_table)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph(
        "VERIFICATION ABSTRACT",
        styles["Section"]
    ))

    abstract = [
        [P("Verification Status", "cell"),
         P("No. of Records", "cell_center"),
         P("Verified / Relevant Quantity", "cell_center")]
    ]

    def add_abs(label, sub):
        if len(sub) == 0:
            return
        if label in ["MISSING / NOT FOUND",
                     "NOT RECEIVED / RECORD DISCREPANCY"]:
            q = int(sub["_Report Missing"].sum())
        else:
            q = int(sub["Verified Available Quantity"].fillna(0).sum())
        abstract.append([
            P(label, "cell"),
            P(len(sub), "cell_center"),
            P(q, "cell_center")
        ])

    add_abs("FOUND / AVAILABLE", found)
    add_abs("PARTIALLY FOUND", partial)
    add_abs("MISSING / NOT FOUND", missing_df)
    add_abs("NOT RECEIVED / RECORD DISCREPANCY", not_received)
    add_abs("SCRAP / WEED-OUT", scrap)
    add_abs("PENDING VERIFICATION", pending)

    # Damaged is a condition, not a separate availability status.
    damaged_count = int(
        df["Condition"].astype(str).str.upper().str.contains(
            "DAMAGED", na=False
        ).sum()
    )

    if damaged_count:
        abstract.append([
            P("DAMAGED CONDITION (physically present)", "cell"),
            P(damaged_count, "cell_center"),
            P("See complete item list", "cell_center")
        ])

    abstract.append([
        P("TOTAL", "cell"),
        P(total_records, "cell_center"),
        P(total_recorded, "cell_center")
    ])

    abs_table = Table(
        abstract,
        colWidths=[130*mm, 45*mm, 95*mm],
        repeatRows=1
    )
    abs_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.45, colors.HexColor("#777777")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#D9EAF7")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#17365D")),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#D9EAF7")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-2),
         [colors.white, colors.HexColor("#F7F9FB")]),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4)
    ]))
    story.append(abs_table)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph(
        "<b>Note:</b> The following pages provide the complete inventory "
        "record in Excel-style tabular form. First, all physically "
        "available/found items are listed. Thereafter, items with other "
        "verification statuses are listed separately. Pending verification "
        "is not treated as missing.",
        styles["small"]
    ))

    story.append(PageBreak())

    # =========================================================
    # TABLE FUNCTION - SIMPLE EXCEL STYLE
    # =========================================================
    def make_item_table(sub):
        """Compact, readable Excel-style inventory table for A4 landscape."""
        headers = [
            "S.No.",
            "Reference No.",
            "Item Details",
            "Bill No. / Date",
            "Avail.\nQty.",
            "Verified\nQty.",
            "Missing\nQty.",
            "Verification\nStatus",
            "Location",
            "Condition"
        ]

        rows = [[P(h, "cell_center") for h in headers]]

        for idx, (_, r) in enumerate(sub.iterrows(), 1):
            item_details = (
                f"<b>{safe(r['Name of the Item'])}</b><br/>"
                f"{safe(r['Inventory Category'])}<br/>"
                f"{safe(r['Inventory Sub Category'])}"
            )

            bill = (
                f"{safe(r['Bill Number']) or '—'}"
                f"<br/>{safe(r['Bill Date']) or '—'}"
            )

            location_parts = [
                val(r["Building"]),
                val(r["Floor"]),
                val(r["Room No"]),
                val(r["Cabin/Lab/Classroom"]),
                val(r["Exact Physical Location"])
            ]
            location_parts = [x for x in location_parts if x]
            location = " → ".join(location_parts) if location_parts else "—"

            rows.append([
                P(idx, "cell_center"),
                P(r["Reference No."] or "—", "cell"),
                Paragraph(item_details, styles["cell"]),
                Paragraph(bill, styles["cell"]),
                P(qty(r["Available Quantity"]), "cell_center"),
                P(qty(r["Verified Available Quantity"]), "cell_center"),
                P(qty(r["_Report Missing"]), "cell_center"),
                P(r["_Report Status"], "cell_center"),
                P(location, "cell"),
                P(r["Condition"] or "—", "cell_center")
            ])

        # A4 landscape printable width ≈ 285 mm with 6 mm margins.
        # These widths total 263 mm, leaving safe space for printers/PDF viewers.
        table = Table(
            rows,
            colWidths=[
                8*mm,   # S.No.
                27*mm,  # Reference
                52*mm,  # Item details
                25*mm,  # Bill
                15*mm,  # Available
                18*mm,  # Verified
                15*mm,  # Missing
                28*mm,  # Status
                55*mm,  # Location
                20*mm   # Condition
            ],
            repeatRows=1,
            splitByRow=1,
            hAlign="LEFT"
        )

        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#8A8A8A")),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#D9EAF7")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#17365D")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("ALIGN", (0,0), (0,-1), "CENTER"),
            ("ALIGN", (4,1), (7,-1), "CENTER"),
            ("ALIGN", (9,1), (9,-1), "CENTER"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.white, colors.HexColor("#F4F8FB")]),
            ("LEFTPADDING", (0,0), (-1,-1), 2),
            ("RIGHTPADDING", (0,0), (-1,-1), 2),
            ("TOPPADDING", (0,0), (-1,-1), 2.5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2.5)
        ]))

        return table

    # =========================================================
    # COMPLETE STATUS-WISE INVENTORY LIST
    # Only sections containing records are printed.
    # No NIL pages and no blank pages.
    # =========================================================
    report_sections = [
        ("A. COMPLETE LIST OF AVAILABLE / FOUND ITEMS",
         found,
         "All inventory records physically found/available during verification."),
        ("B. PARTIALLY FOUND ITEMS",
         partial,
         "Recorded quantity is greater than the physically verified quantity."),
        ("C. MISSING / NOT FOUND ITEMS",
         missing_df,
         "Items/quantities not physically accounted for during verification."),
        ("D. NOT RECEIVED / RECORD DISCREPANCY",
         not_received,
         "Items identified as not received or requiring record reconciliation."),
        ("E. SCRAP / WEED-OUT ITEMS",
         scrap,
         "Items explicitly identified as scrap/weed-out in the verification data."),
        ("F. PENDING VERIFICATION",
         pending,
         "Verification is incomplete. Pending items are not treated as missing.")
    ]

    nonempty_sections = [
        (title, subset, note)
        for title, subset, note in report_sections
        if len(subset) > 0
    ]

    for section_index, (title, subset, note) in enumerate(nonempty_sections):
        # Start every actual section on a new page, but never create
        # a page for an empty/NIL section.
        if section_index > 0:
            story.append(PageBreak())

        story.append(Paragraph(title, styles["Section"]))
        story.append(Paragraph(note, styles["small"]))
        story.append(Spacer(1, 2.5*mm))
        story.append(make_item_table(subset))

    # =========================================================
    # FINAL DECLARATION / SIGNATURES
    # =========================================================
    story.append(PageBreak())
    story.append(Paragraph(
        "G. DEPARTMENTAL DECLARATION AND CERTIFICATION",
        styles["Section"]
    ))

    declaration = (
        "Certified that the inventory listed in this report has been physically "
        "verified against the inventory records made available for the "
        "verification exercise. The item-wise availability, verified quantity, "
        "missing quantity, verification status, condition and physical location "
        "shown in this report are based on the verification information recorded "
        "for the department. Discrepancies identified in the report may be "
        "subject to further reconciliation and necessary administrative action."
    )

    story.append(Paragraph(declaration, styles["small"]))
    story.append(Spacer(1, 7*mm))

    sign_rows = [
        [P("Verification Committee Member", "cell"),
         P("Name / Designation", "cell"),
         P("Signature", "cell")],
        [P("1.", "cell"), P(""), P("")],
        [P("2.", "cell"), P(""), P("")],
        [P("3.", "cell"), P(""), P("")],
        [P("4.", "cell"), P(""), P("")],
        [P("Department Head / HOD", "cell"), P(""), P("")]
    ]

    sign_table = Table(
        sign_rows,
        colWidths=[70*mm, 100*mm, 70*mm],
        rowHeights=[8*mm, 13*mm, 13*mm, 13*mm, 13*mm, 15*mm]
    )
    sign_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#777777")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF2F8")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4)
    ]))
    story.append(sign_table)
    story.append(Spacer(1, 7*mm))

    final_table = Table([
        [P("HOD Name", "cell"), P(""),
         P("Verification Date", "cell"), P(report_date, "cell")],
        [P("HOD Signature", "cell"), P(""),
         P("Official Seal", "cell"), P("")],
    ], colWidths=[35*mm, 95*mm, 40*mm, 70*mm])

    final_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#777777")),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F1F5F9")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#F1F5F9")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7)
    ]))
    story.append(final_table)

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    return pdf_file
