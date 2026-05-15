import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from generate_department_report import generate_pdf_report

# =====================================================
# GOOGLE AUTH
# =====================================================

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'config/credentials.json',
    scope
)

client = gspread.authorize(credentials)

# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title='CSJMU Live Inventory Dashboard',
    layout='wide'
)

st.title('CSJMU Live Inventory Verification Dashboard')

# =====================================================
# GOOGLE SHEETS CONFIG
# =====================================================

DEPARTMENTS = {

    'UIBM': 'UIBM',
    'ATAL': 'ATAL'

}

# =====================================================
# SUMMARY
# =====================================================

summary_data = []

department_data = {}

for dept, sheet_name in DEPARTMENTS.items():

    try:

        # ==============================================
        # READ GOOGLE SHEET
        # ==============================================

        sheet = client.open(sheet_name).get_worksheet(0)

        data = sheet.get_all_records()

        df = pd.DataFrame(data)

        department_data[dept] = df

        # ==============================================
        # SAFE COLUMNS
        # ==============================================

        required_columns = [

            'Total Quantity',
            'Available Quantity',
            'Verified Available Quantity',
            'Missing Quantity',
            'Verification Status',
            'Condition'

        ]

        for col in required_columns:

            if col not in df.columns:

                df[col] = 0

        # ==============================================
        # CALCULATIONS
        # ==============================================

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

        pending_items = len(
            df[
                df['Verification Status']
                .astype(str)
                .str.upper()
                .isin(['', 'PENDING', 'NONE'])
            ]
        )

        damaged_assets = len(
            df[
                df['Condition']
                .astype(str)
                .str.upper()
                == 'DAMAGED'
            ]
        )

        # ==============================================
        # SUMMARY APPEND
        # ==============================================

        summary_data.append({

            'Department': dept,

            'Total Items': total_items,

            'Total Quantity': total_quantity,

            'Available Quantity': available_quantity,

            'Verified Quantity': verified_quantity,

            'Missing Quantity': missing_quantity,

            'Pending Items': pending_items,

            'Damaged Assets': damaged_assets

        })

    except Exception as e:

        st.error(f'Error reading {dept}: {e}')

# =====================================================
# SHOW SUMMARY
# =====================================================

summary_df = pd.DataFrame(summary_data)

st.subheader('Department-wise Summary')

st.dataframe(
    summary_df,
    use_container_width=True
)

# =====================================================
# DETAILED VIEW
# =====================================================

st.markdown('---')

selected_department = st.selectbox(
    'Select Department',
    list(DEPARTMENTS.keys())
)

# =====================================================
# SHOW DETAILS
# =====================================================

if selected_department:

    df = department_data[selected_department]

    st.subheader(
        f'Detailed Inventory Information - {selected_department}'
    )

    columns_to_show = [

        'Reference No.',
        'Name of the Item',
        'Inventory Category',
        'Inventory Sub Category',
        'Total Quantity',
        'Available Quantity',
        'Building',
        'Floor',
        'Room No',
        'Cabin/Lab/Classroom',
        'Exact Physical Location',
        'Custodian/User',
        'Department Verification Committee',
        'Verified Available Quantity',
        'Missing Quantity',
        'Verification Status',
        'Condition',
        'QR Sticker Pasted',
        'Verified By',
        'Verification Date',
        'Remarks'

    ]

    available_columns = [

        col for col in columns_to_show

        if col in df.columns

    ]

    st.dataframe(
        df[available_columns],
        use_container_width=True,
        height=650
    )

    # =================================================
    # GENERATE PDF REPORT BUTTON
    # =================================================

    st.markdown('---')

    if st.button('Generate Final Department Report'):

        try:

            generate_pdf_report(
                selected_department,
                df
            )

            st.success(
                f'{selected_department} PDF Report Generated Successfully!'
            )

            st.info(
                'Check folder: D:\\VERIFIED_DEPARTMENT_FILES\\final_reports'
            )

        except Exception as e:

            st.error(f'PDF Generation Error: {e}')

# =====================================================
# FOOTER
# =====================================================

st.markdown('---')

st.caption(
    'CSJMU QR-Based Inventory Verification & Monitoring System'
)