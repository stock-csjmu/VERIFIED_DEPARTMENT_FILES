import streamlit as st
import pandas as pd
import os

# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FOLDER = "input_excels"

# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="CSJMU Inventory Dashboard",
    layout="wide"
)

# =====================================================
# TITLE
# =====================================================

st.title("CSJMU Live Inventory Verification Dashboard")

# =====================================================
# READ DEPARTMENT FILES
# =====================================================

department_files = {}

for file in os.listdir(INPUT_FOLDER):

    if file.endswith(".xlsx"):

        department_name = file.replace(".xlsx", "")

        department_files[department_name] = os.path.join(
            INPUT_FOLDER,
            file
        )

# =====================================================
# SUMMARY TABLE
# =====================================================

summary_data = []

for dept, file_path in department_files.items():

    try:

        df = pd.read_excel(file_path)

        # ---------------------------------------------
        # SAFE COLUMN CREATION
        # ---------------------------------------------

        required_columns = [
            'Total Quantity',
            'Available Quantity',
            'Verified Available Quantity',
            'Missing Quantity',
            'Condition',
            'Verification Status',
            'Verification Date'
        ]

        for col in required_columns:

            if col not in df.columns:

                df[col] = 0

        # ---------------------------------------------
        # CALCULATIONS
        # ---------------------------------------------

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

        missing_quantity = (
            total_quantity - verified_quantity
        )

        pending_quantity = (
            total_quantity - verified_quantity
        )

        pending_items = len(
            df[
                pd.to_numeric(
                    df['Verified Available Quantity'],
                    errors='coerce'
                ).fillna(0) == 0
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

        last_verification = ""

        try:

            non_empty_dates = df[
                df['Verification Date'].notna()
            ]

            if len(non_empty_dates) > 0:

                last_verification = str(
                    non_empty_dates[
                        'Verification Date'
                    ].iloc[-1]
                )

        except:
            last_verification = ""

        # ---------------------------------------------
        # APPEND SUMMARY
        # ---------------------------------------------

        summary_data.append({

            'Department': dept,

            'Total Items': total_items,

            'Total Quantity': total_quantity,

            'Available Quantity': available_quantity,

            'Verified Quantity': verified_quantity,

            'Missing Quantity': missing_quantity,

            'Pending Quantity': pending_quantity,

            'Pending Items': pending_items,

            'Damaged Assets': damaged_assets,

            'Last Verification': last_verification

        })

    except Exception as e:

        st.error(f"Error reading {dept}: {e}")

# =====================================================
# SHOW SUMMARY
# =====================================================

summary_df = pd.DataFrame(summary_data)

st.subheader("Department-wise Summary")

st.dataframe(
    summary_df,
    use_container_width=True
)

# =====================================================
# DETAILED VIEW
# =====================================================

st.markdown("---")

selected_department = st.selectbox(
    "Select Department for Detailed Information",
    list(department_files.keys())
)

# =====================================================
# SHOW DETAILS
# =====================================================

if selected_department:

    file_path = department_files[selected_department]

    df = pd.read_excel(file_path)

    st.subheader(
        f"Detailed Inventory Information - {selected_department}"
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

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.caption(
    "CSJMU QR-Based Inventory Verification & Monitoring System"
)