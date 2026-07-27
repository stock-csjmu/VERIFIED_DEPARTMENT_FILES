import streamlit as st
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from generate_department_report import generate_pdf_report

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="CSJMU Live Inventory Dashboard",
    layout="wide"
)

st.title("CSJMU Live Inventory Verification Dashboard")

# =========================================================
# GOOGLE AUTHENTICATION
# =========================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials_dict = dict(st.secrets["gcp_service_account"])

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    credentials_dict,
    scope
)

client = gspread.authorize(credentials)

# =========================================================
# LOAD DEPARTMENT CONFIGURATION
# =========================================================

departments_df = pd.read_csv("departments.csv")

department_sheets = dict(
    zip(
        departments_df["Department"],
        departments_df["SheetID"]
    )
)

# =========================================================
# LOAD GOOGLE SHEET DATA
# =========================================================

@st.cache_data(ttl=600)
def load_department_data(sheet_id):

    spreadsheet = client.open_by_key(sheet_id)

    worksheet = spreadsheet.sheet1

    data = worksheet.get_all_records()

    df = pd.DataFrame(data)

    return df

# =========================================================
# SUMMARY DATA
# =========================================================

summary_data = []

department_dataframes = {}



# =========================================================
# SUMMARY TABLE
# =========================================================

st.subheader("Department-wise Summary")

st.info(
    "Summary is loaded for the selected department only to improve performance."
)

# =========================================================
# DEPARTMENT SELECTION
# =========================================================

st.divider()

selected_department = st.selectbox(
    "Select Department",
    list(department_sheets.keys())
)
sheet_id = department_sheets[selected_department]

detail_df = load_department_data(sheet_id)

# =========================================================
# DETAIL DATAFRAME
# =========================================================

detail_df = load_department_data(sheet_id)

# =========================================================
# SAFE NUMERIC CONVERSION
# =========================================================

detail_df["Total Quantity"] = pd.to_numeric(
    detail_df["Total Quantity"],
    errors="coerce"
).fillna(0)

detail_df["Verified Available Quantity"] = pd.to_numeric(
    detail_df["Verified Available Quantity"],
    errors="coerce"
).fillna(0)

# =========================================================
# ROW LEVEL MISSING QUANTITY
# =========================================================

detail_df["Missing Quantity"] = (
    detail_df["Total Quantity"] -
    detail_df["Verified Available Quantity"]
)

# =========================================================
# DETAIL SECTION
# =========================================================

st.subheader(
    f"Detailed Inventory Information - {selected_department}"
)

display_columns = [
    "Reference No.",
    "Name of the Item",
    "Inventory Category",
    "Inventory Sub Category",
    "Total Quantity",
    "Available Quantity",
    "Building",
    "Floor",
    "Room No",
    "Cabin/Lab/Classroom",
    "Exact Physical Location",
    "Custodian/User",
    "Department Verification Committee",
    "Verified Available Quantity",
    "Missing Quantity",
    "Verification Status",
    "Condition",
    "QR Sticker Pasted",
    "Verified By",
    "Verification Date",
    "Remarks"
]

available_columns = [
    col for col in display_columns
    if col in detail_df.columns
]

st.dataframe(
    detail_df[available_columns],
    use_container_width=True
)

# =========================================================
# PDF REPORT GENERATION
# =========================================================

st.divider()

if st.button("Generate Final Department Report"):

    pdf_file = generate_pdf_report(
        selected_department,
        detail_df
    )

    with open(pdf_file, "rb") as file:

        st.download_button(
            label="Download Department Verification Report",
            data=file,
            file_name=pdf_file,
            mime="application/pdf"
        )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "CSJMU QR-Based Inventory Verification & Monitoring System"
)