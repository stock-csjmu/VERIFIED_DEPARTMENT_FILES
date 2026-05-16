from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

import pandas as pd


def generate_pdf_report(department_name, df):

    # =========================================
    # FILE NAME
    # =========================================

    file_name = f"{department_name}_Verification_Report.pdf"

    # =========================================
    # PDF DOCUMENT
    # =========================================

    doc = SimpleDocTemplate(
        file_name,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    elements = []

    # =========================================
    # TITLE
    # =========================================

    title = Paragraph(
        "<b>CHHATRAPATI SHAHU JI MAHARAJ UNIVERSITY</b>",
        styles['Title']
    )

    subtitle = Paragraph(
        f"<b>{department_name} - Inventory Verification Completion Report</b>",
        styles['Heading2']
    )

    elements.append(title)
    elements.append(Spacer(1, 12))

    elements.append(subtitle)
    elements.append(Spacer(1, 20))

    # =========================================
    # SAFE NUMERIC CONVERSION
    # =========================================

    df["Total Quantity"] = pd.to_numeric(
        df["Total Quantity"],
        errors="coerce"
    ).fillna(0)

    df["Verified Available Quantity"] = pd.to_numeric(
        df["Verified Available Quantity"],
        errors="coerce"
    ).fillna(0)

    # =========================================
    # SUMMARY CALCULATIONS
    # =========================================

    total_items = len(df)

    total_quantity = int(df["Total Quantity"].sum())

    verified_quantity = int(
        df["Verified Available Quantity"].sum()
    )

    missing_quantity = (
        total_quantity - verified_quantity
    )

    damaged_assets = len(
        df[
            df["Condition"]
            .astype(str)
            .str.upper()
            == "DAMAGED"
        ]
    )

    pending_items = len(
        df[
            df["Verified Available Quantity"] == 0
        ]
    )

    # =========================================
    # SUMMARY TABLE
    # =========================================

    summary_data = [
        ["Department", department_name],
        ["Total Inventory Items", total_items],
        ["Total Quantity", total_quantity],
        ["Verified Quantity", verified_quantity],
        ["Missing Quantity", missing_quantity],
        ["Damaged Assets", damaged_assets],
        ["Pending Verification", pending_items]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[220, 220]
    )

    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # EXCEPTION ITEMS ONLY
    # =========================================

    exception_df = df[
        (
            df["Total Quantity"] -
            df["Verified Available Quantity"]
        ) > 0
    ].copy()

    # =========================================
    # CALCULATE ROW MISSING
    # =========================================

    exception_df["Missing Qty"] = (
        exception_df["Total Quantity"] -
        exception_df["Verified Available Quantity"]
    )

    # =========================================
    # HEADING
    # =========================================

    exception_heading = Paragraph(
        "<b>Exception / Discrepancy Items</b>",
        styles['Heading3']
    )

    elements.append(exception_heading)

    elements.append(Spacer(1, 10))

    # =========================================
    # TABLE DATA
    # =========================================

    table_data = [[
        "Asset ID",
        "Name of Item",
        "Missing Qty",
        "Verification Status",
        "Condition"
    ]]

    for _, row in exception_df.iterrows():

        table_data.append([
            str(row.get("Reference No.", "")),
            str(row.get("Name of the Item", ""))[:40],
            str(int(row.get("Missing Qty", 0))),
            str(row.get("Verification Status", "")),
            str(row.get("Condition", ""))
        ])

    # =========================================
    # EXCEPTION TABLE
    # =========================================

    exception_table = Table(
        table_data,
        colWidths=[100, 200, 70, 90, 70],
        repeatRows=1
    )

    exception_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),

        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))

    elements.append(exception_table)

    elements.append(Spacer(1, 30))

    # =========================================
    # COMMITTEE DECLARATION
    # =========================================

    declaration_heading = Paragraph(
        "<b>Committee Declaration</b>",
        styles['Heading3']
    )

    declaration_text = Paragraph(
        """
        The inventory verification of the department has been
        physically conducted by the undersigned committee members.
        The above details are verified and found correct as per
        available records and physical stock condition.
        """,
        styles['BodyText']
    )

    elements.append(declaration_heading)

    elements.append(Spacer(1, 8))

    elements.append(declaration_text)

    elements.append(Spacer(1, 25))

    # =========================================
    # SIGNATURE TABLE
    # =========================================

    signature_data = [
        ["Verification Committee Members", ""],
        ["1. ____________________", ""],
        ["2. ____________________", ""],
        ["3. ____________________", ""],
        ["", ""],
        ["Department Head", "________________"],
        ["Verification Date", "________________"]
    ]

    signature_table = Table(
        signature_data,
        colWidths=[250, 200]
    )

    signature_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(signature_table)

    # =========================================
    # BUILD PDF
    # =========================================

    doc.build(elements)

    return file_name