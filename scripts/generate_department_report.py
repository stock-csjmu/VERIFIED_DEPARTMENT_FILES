from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

import pandas as pd
import os


def generate_pdf_report(department_name, df):

    # =====================================================
    # OUTPUT FOLDER
    # =====================================================

    output_folder = r"D:\VERIFIED_DEPARTMENT_FILES\final_reports"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(
        output_folder,
        f"{department_name}_Final_Verification_Report.pdf"
    )

    # =====================================================
    # PDF DOCUMENT
    # =====================================================

    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    elements = []

    # =====================================================
    # TITLE
    # =====================================================

    title = Paragraph(

        "<b>CHHATRAPATI SHAHU JI MAHARAJ UNIVERSITY</b>",

        styles['Title']
    )

    subtitle = Paragraph(

        f"<b>{department_name} - Inventory Verification Completion Report</b>",

        styles['Heading2']
    )

    elements.append(title)
    elements.append(Spacer(1, 10))

    elements.append(subtitle)
    elements.append(Spacer(1, 25))

    # =====================================================
    # SAFE COLUMNS
    # =====================================================

    numeric_columns = [

        'Total Quantity',
        'Available Quantity',
        'Verified Available Quantity',
        'Missing Quantity'

    ]

    for col in numeric_columns:

        if col not in df.columns:

            df[col] = 0

    # =====================================================
    # CALCULATIONS
    # =====================================================

    total_items = len(df)

    total_quantity = pd.to_numeric(
        df['Total Quantity'],
        errors='coerce'
    ).fillna(0).sum()

    available_quantity = pd.to_numeric(
        df['Available Quantity'],
        errors='coerce'
    ).fillna(0).sum()

    verified_quantity = pd.to_numeric(
        df['Verified Available Quantity'],
        errors='coerce'
    ).fillna(0).sum()

    missing_quantity = pd.to_numeric(
        df['Missing Quantity'],
        errors='coerce'
    ).fillna(0).sum()

    damaged_assets = len(
        df[
            df['Condition']
            .astype(str)
            .str.upper()
            == 'DAMAGED'
        ]
    )

    pending_items = len(
        df[
            df['Verification Status']
            .astype(str)
            .str.upper()
            .isin(['', 'PENDING', 'NONE'])
        ]
    )

    # =====================================================
    # SUMMARY TABLE
    # =====================================================

    summary_data = [

        ['Department', department_name],

        ['Total Inventory Items', total_items],

        ['Total Quantity', int(total_quantity)],

        ['Available Quantity', int(available_quantity)],

        ['Verified Quantity', int(verified_quantity)],

        ['Missing Quantity', int(missing_quantity)],

        ['Damaged Assets', damaged_assets],

        ['Pending Verification', pending_items]

    ]

    summary_table = Table(

        summary_data,

        colWidths=[220, 220]

    )

    summary_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),

        ('FONTSIZE', (0, 0), (-1, -1), 10),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)

    ]))

    elements.append(summary_table)

    elements.append(Spacer(1, 30))

    # =====================================================
    # EXCEPTION ITEMS ONLY
    # =====================================================

    exception_df = df[

        (
            pd.to_numeric(
                df['Missing Quantity'],
                errors='coerce'
            ).fillna(0) > 0
        )

        |

        (
            df['Condition']
            .astype(str)
            .str.upper()
            == 'DAMAGED'
        )

        |

        (
            ~df['Verification Status']
            .astype(str)
            .str.upper()
            .isin(['FOUND', 'VERIFIED'])
        )

    ]

    # =====================================================
    # EXCEPTION SECTION
    # =====================================================

    elements.append(

        Paragraph(

            "<b>Exception / Discrepancy Items</b>",

            styles['Heading3']
        )

    )

    elements.append(Spacer(1, 10))

    # =====================================================
    # IF EXCEPTION EXISTS
    # =====================================================

    if len(exception_df) > 0:

        exception_columns = [

            'Asset ID',
            'Name of the Item',
            'Missing Quantity',
            'Verification Status',
            'Condition'

        ]

        available_exception_columns = [

            col for col in exception_columns

            if col in exception_df.columns

        ]

        table_data = [available_exception_columns]

        for _, row in exception_df.iterrows():

            table_data.append([

                str(row.get(col, ''))[:40]

                for col in available_exception_columns

            ])

        exception_table = Table(

            table_data,

            colWidths=[90, 200, 70, 80, 80]

        )

        exception_table.setStyle(TableStyle([

            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),

            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

            ('GRID', (0, 0), (-1, -1), 1, colors.black),

            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            ('FONTSIZE', (0, 0), (-1, -1), 8),

            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)

        ]))

        elements.append(exception_table)

    else:

        elements.append(

            Paragraph(

                "No discrepancy items found. All inventory verified successfully.",

                styles['BodyText']
            )

        )

    elements.append(Spacer(1, 40))

    # =====================================================
    # DECLARATION
    # =====================================================

    declaration = Paragraph(

        """
        <b>Committee Declaration:</b><br/><br/>

        The inventory verification of the department has been physically
        conducted by the undersigned committee members.

        The above details are verified and found correct
        as per available records and physical stock condition.

        """,

        styles['BodyText']

    )

    elements.append(declaration)

    elements.append(Spacer(1, 40))

    # =====================================================
    # SIGNATURE TABLE
    # =====================================================

    signature_data = [

        ['Verification Committee Members', ''],

        ['1. _____________________', ''],

        ['2. _____________________', ''],

        ['3. _____________________', ''],

        ['', ''],

        ['Department Head', '__________________'],

        ['Verification Date', '__________________']

    ]

    signature_table = Table(

        signature_data,

        colWidths=[250, 220]

    )

    signature_table.setStyle(TableStyle([

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),

        ('FONTSIZE', (0, 0), (-1, -1), 10),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 10)

    ]))

    elements.append(signature_table)

    # =====================================================
    # BUILD PDF
    # =====================================================

    doc.build(elements)

    print(f"Professional PDF Generated: {output_file}")