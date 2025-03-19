import streamlit as st
import pandas as pd

# Import your helper class
from helper.gsheet_connection import GsheetConnection

# Configuration
TOKEN_JSON = dict(st.secrets["gsheet_auth"]["sheet_token_json"])
SCOPES = st.secrets["gsheet_auth"]["SCOPES"]
SPREADSHEET_ID = st.secrets["gsheet_auth"]["SPREADSHEET_ID"]
SHEET_NAME = st.secrets["gsheet_auth"]["SHEET_NAME"]

# Initialize Google Sheets connection
gsheet = GsheetConnection(TOKEN_JSON, SCOPES, SPREADSHEET_ID, SHEET_NAME)

st.title("✏️ Edit Asset Details")

# Ensure selected_item exists in session
if "selected_item" not in st.session_state:
    st.error("⚠️ No asset selected. Please go back and select an asset.")
    st.stop()

# Get selected asset
asset = st.session_state.selected_item

# Load all data to find row index
df = gsheet.get_data()
row_index = df.index[df["Nomor Asset"] == asset["Nomor Asset"]].tolist()

if not row_index:
    st.error("❌ Asset not found in the database!")
    st.stop()

row_index = row_index[0]  # Get the actual index

# Editable form
with st.form(key="edit_form"):
    st.subheader("📄 Asset Information")
    asset_no = st.text_input("🆔 Nomor Asset", asset["Nomor Asset"], disabled=True)
    nama_asset = st.text_input("🏷️ Nama Asset", asset["Nama Asset"])
    lokasi = st.text_input("📍 Penempatan Aset", asset["PENEMPATAN ASET"])
    sumber = st.text_input("🔗 Sumber", asset["Sumber"])
    kelompok_aset = st.text_input("🏷️ Kelompok Aset", asset["Kelompok Aset"])
    kepemilikan = st.text_input("📝 Kepemilikan", asset["Kepemilikan"])
    qty = st.number_input("📊 Qty", min_value=0, value=int(asset["Qty"]))
    harga_perolehan = st.number_input("💰 Harga Perolehan", min_value=0, value=int(asset["Harga Perolehan"]))

    st.subheader("📆 Purchase Details")
    tahun_beli = st.number_input("Tahun Beli", min_value=1900, max_value=2100, value=int(asset["Tahun Beli"]))
    bulan_beli = st.text_input("Bulan Beli", asset["Bulan Beli"])
    umur_ekonomis = st.number_input("📈 Umur Ekonomis (years)", min_value=0, value=int(asset["Umur Ekonomis"]))
    penyusutan = st.number_input("📉 Nilai Penyusutan per Bulan", min_value=0, value=int(asset["Nilai Penyusutan per Bulan"]))

    st.subheader("💎 Asset Valuation")
    valuasi_fields = ["VALUASI ASSET 2019", "VALUASI ASSET 2020", "VALUASI ASSET 2021", "VALUASI ASSET 2022",
                      "VALUASI ASSET 2023", "VALUASI ASSET 2024", "VALUASI ASSET 2025", "Nilai Buku 2024"]
    
    valuations = {field: st.number_input(f"💎 {field}", min_value=0, value=int(asset[field])) for field in valuasi_fields}

    st.subheader("📌 Status")
    status = st.text_input("📌 Status", asset["Status"])
    label = st.text_input("🔖 Label", asset["Label"])

    # Submit button
    submitted = st.form_submit_button("✅ Update Asset")

if submitted:
    # Prepare updated values
    update_values = [
        nama_asset, lokasi, sumber, kelompok_aset, kepemilikan, qty, harga_perolehan,
        tahun_beli, bulan_beli, umur_ekonomis, penyusutan, *valuations.values(), status, label
    ]
    
    # Update the row in Google Sheets
    gsheet.update_data(row_index, update_values)

    st.success("✅ Asset details updated successfully!")

    # Update session state
    for key, value in zip(["Nama Asset", "PENEMPATAN ASET", "Sumber", "Kelompok Aset", "Kepemilikan", "Qty", "Harga Perolehan",
                           "Tahun Beli", "Bulan Beli", "Umur Ekonomis", "Nilai Penyusutan per Bulan", *valuasi_fields, "Status", "Label"], update_values):
        st.session_state.selected_item[key] = value

# Back button
if st.button("⬅️ Back to Asset Details"):
    st.switch_page("pages/detail_products.py")
