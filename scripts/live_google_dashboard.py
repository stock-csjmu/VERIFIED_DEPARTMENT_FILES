from pathlib import Path

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from generate_department_report import generate_pdf_report


BASE_DIR = Path(__file__).resolve().parent.parent
DEPARTMENTS_FILE = BASE_DIR / "departments.csv"

st.set_page_config(
    page_title="CSJMU Live Inventory Dashboard",
    layout="wide"
)

st.title("CSJMU Live Inventory Verification Dashboard")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# =========================================================
# GOOGLE AUTHENTICATION
# Local PC       -> config/credentials.json
# Streamlit Cloud -> st.secrets
# =========================================================

credentials_file = BASE_DIR / "config" / "credentials.json"

try:
    # Streamlit Cloud
    credentials_dict = dict(
        st.secrets["gcp_service_account"]
    )

    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        credentials_dict,
        scope
    )

except Exception:
    # Local PC
    if not credentials_file.exists():
        st.error(
            f"Google credentials file not found: {credentials_file}"
        )
        st.stop()

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        str(credentials_file),
        scope
    )

client = gspread.authorize(credentials)

departments_df = pd.read_csv(DEPARTMENTS_FILE)

departments_df["Department"] = departments_df["Department"].astype(str).str.strip()
departments_df["SheetID"] = departments_df["SheetID"].astype(str).str.strip()

departments_df = departments_df[
    (departments_df["Department"] != "") &
    (departments_df["SheetID"] != "")
].copy()

department_sheets = dict(
    zip(departments_df["Department"], departments_df["SheetID"])
)


def make_unique_headers(headers):
    result = []
    used = {}

    for position, header in enumerate(headers, start=1):
        header = str(header).strip()

        if not header:
            header = f"Column_{position}"

        if header not in used:
            used[header] = 1
            result.append(header)
        else:
            used[header] += 1
            result.append(f"{header}_{used[header]}")

    return result


@st.cache_data(ttl=600)
def load_department_data(sheet_id):
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    # Use get_all_values() instead of get_all_records().
    # This avoids GSpreadException when a new sheet has duplicate
    # or blank header cells.
    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    headers = make_unique_headers(values[0])
    data_rows = values[1:]

    if not data_rows:
        return pd.DataFrame(columns=headers)

    normalized_rows = []

    for row in data_rows:
        row = list(row)

        if len(row) < len(headers):
            row.extend([""] * (len(headers) - len(row)))
        elif len(row) > len(headers):
            row = row[:len(headers)]

        normalized_rows.append(row)

    df = pd.DataFrame(normalized_rows, columns=headers)
    return df.dropna(how="all")


st.subheader("Department-wise Summary")

st.info(
    "Summary is loaded for the selected department only to improve performance."
)

st.divider()

selected_department = st.selectbox(
    "Select Department",
    list(department_sheets.keys())
)

sheet_id = department_sheets[selected_department]

try:
    detail_df = load_department_data(sheet_id)

except Exception as e:
    st.error(
        f"Unable to read the Google Sheet for {selected_department}."
    )
    st.warning(
        "Please check the Sheet ID, first worksheet, and Google service-account access."
    )
    st.exception(e)
    st.stop()

if detail_df.empty:
    st.warning(
        f"The first worksheet of {selected_department} is empty."
    )
    st.stop()

if "Total Quantity" in detail_df.columns:
    detail_df["Total Quantity"] = pd.to_numeric(
        detail_df["Total Quantity"], errors="coerce"
    ).fillna(0)
else:
    detail_df["Total Quantity"] = 0

if "Verified Available Quantity" in detail_df.columns:
    detail_df["Verified Available Quantity"] = pd.to_numeric(
        detail_df["Verified Available Quantity"], errors="coerce"
    ).fillna(0)
else:
    detail_df["Verified Available Quantity"] = 0

detail_df["Missing Quantity"] = (
    detail_df["Total Quantity"] -
    detail_df["Verified Available Quantity"]
)

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

st.divider()

if st.button("Generate Final Department Report"):
    try:
        pdf_file = generate_pdf_report(
            selected_department,
            detail_df.copy()
        )

        with open(pdf_file, "rb") as file:
            pdf_data = file.read()

        st.download_button(
            label="Download Department Verification Report",
            data=pdf_data,
            file_name=Path(pdf_file).name,
            mime="application/pdf"
        )

    except Exception as e:
        st.error("Unable to generate the department report.")
        st.exception(e)

st.divider()

st.caption(
    "CSJMU QR-Based Inventory Verification & Monitoring System"
)
