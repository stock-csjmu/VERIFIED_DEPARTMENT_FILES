import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================================
# PAGE CONFIGURATION
# =========================================

st.set_page_config(
    page_title="CSJMU Live Inventory Dashboard",
    layout="wide"
)

st.title("CSJMU Live Inventory Verification Dashboard")

# =========================================
# GOOGLE API AUTHENTICATION
# =========================================

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

# =========================================
# LOAD DEPARTMENT CONFIGURATION
# =========================================

departments_df = pd.read_csv("departments.csv")

department_sheets = dict(
    zip(
        departments_df["Department"],
        departments_df["SheetID"]
    )
)

# =========================================
# LOAD GOOGLE SHEET DATA
# =========================================

@st.cache_data(ttl=60)
def load_department_data(sheet_id):

    spreadsheet = client.open_by_key(sheet_id)

    worksheet = spreadsheet.sheet1

    data = worksheet.get_all_records()

    df = pd.DataFrame(data)

    return df

# =========================================
# SUMMARY SECTION
# =========================================

summary_data = []

department_dataframes = {}

for department_name, sheet_id in department_sheets.items():

    try:

        df = load_department_data(sheet_id)

        department_dataframes[department_name] = df

        df["Total Quantity"] = pd.to_numeric(
            df["Total Quantity"],
            errors="coerce"
        ).fillna(0)

        df["Verified Available Quantity"] = pd.to_numeric(
            df["Verified Available Quantity"],
            errors="coerce"
        ).fillna(0)

        df["Calculated Missing Quantity"] = (
            df["Total Quantity"] -
            df["Verified Available Quantity"]
        )

        total_items = len(df)

        total_quantity = df["Total Quantity"].sum()

        verified_quantity = df["Verified Available Quantity"].sum()

        missing_quantity = (
            total_quantity - verified_quantity
        )

        pending_items = len(
            df[df["Verified Available Quantity"] == 0]
        )

        damaged_assets = len(
            df[
                df["Condition"]
                .astype(str)
                .str.upper()
                == "DAMAGED"
            ]
        )

        summary = {
            "Department": department_name,
            "Total Items": int(total_items),
            "Total Quantity": int(total_quantity),
            "Available Quantity": int(total_quantity),
            "Verified Quantity": int(verified_quantity),
            "Missing Quantity": int(missing_quantity),
            "Pending Items": int(pending_items),
            "Damaged Assets": int(damaged_assets)
        }

        summary_data.append(summary)

    except Exception as e:

        st.error(f"Error reading {department_name}: {e}")

# =========================================
# DISPLAY SUMMARY
# =========================================

st.subheader("Department-wise Summary")

summary_df = pd.DataFrame(summary_data)

st.dataframe(
    summary_df,
    use_container_width=True
)

# =========================================
# SELECT DEPARTMENT
# =========================================

st.divider()

selected_department = st.selectbox(
    "Select Department",
    list(department_sheets.keys())
)

# =========================================
# DETAIL TABLE
# =========================================

st.subheader(
    f"Detailed Inventory Information - {selected_department}"
)

detail_df = department_dataframes[selected_department]

detail_df["Total Quantity"] = pd.to_numeric(
    detail_df["Total Quantity"],
    errors="coerce"
).fillna(0)

detail_df["Verified Available Quantity"] = pd.to_numeric(
    detail_df["Verified Available Quantity"],
    errors="coerce"
).fillna(0)

detail_df["Calculated Missing Quantity"] = (
    detail_df["Total Quantity"] -
    detail_df["Verified Available Quantity"]
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
    "Calculated Missing Quantity",
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

# =========================================
# FOOTER
# =========================================

st.divider()

st.caption(
    "CSJMU QR-Based Inventory Verification & Monitoring System"
)