import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
import pandas as pd
from helper.gsheet_connection import GsheetConnection  
import textwrap


# Configuration
TOKEN_JSON = dict(st.secrets["gsheet_auth"]["sheet_token_json"])
SCOPES = st.secrets["gsheet_auth"]["SCOPES"]
SPREADSHEET_ID = st.secrets["gsheet_auth"]["SPREADSHEET_ID"]
SHEET_NAME = st.secrets["gsheet_auth"]["SHEET_NAME"]

# Initialize Google Sheets Connection
gsheet = GsheetConnection(TOKEN_JSON, SCOPES, SPREADSHEET_ID, SHEET_NAME)

from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO

def generate_label(nomor_asset, kepemilikan, nama_asset):
    # Define label size (60mm x 40mm in pixels at 96 DPI)
    label_width, label_height = 227, 151  

    # Create blank label (white background)
    label = Image.new("RGB", (label_width, label_height), "white")
    draw = ImageDraw.Draw(label)

    # Generate QR Code
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(nomor_asset)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    # Resize QR Code to fit within the label
    qr_size = 90  
    qr_img = qr_img.resize((qr_size, qr_size))

    # Load a font
    try:
        font = ImageFont.truetype("arial.ttf", 14)  
    except IOError:
        font = ImageFont.load_default()

    # Position QR Code (left side)
    qr_x = 5
    qr_y = (label_height - qr_size) // 2
    label.paste(qr_img, (qr_x, qr_y))

    # Text positions (right of QR Code)
    text_x = qr_x + qr_size + 5  
    text_y = qr_y + 7

    # Wrap text for Nama Asset (Max 2 Lines)
    max_width = label_width - text_x - 5  
    wrapped_lines = textwrap.wrap(nama_asset, width=20)  
    if len(wrapped_lines) > 2:
        wrapped_nama_asset = wrapped_lines[:2]  # Take only first 2 lines
        wrapped_nama_asset[-1] += "..."  # Add ellipses if exceeded
    else:
        wrapped_nama_asset = wrapped_lines

    # Draw text in order
    draw.text((text_x, text_y), f"{nomor_asset}", font=font, fill="black")  # Nomor Asset
    draw.text((text_x, text_y + 20), f"{kepemilikan}", font=font, fill="black")  # Kepemilikan
    
    # Draw wrapped Nama Asset with max 2 lines
    for i, line in enumerate(wrapped_nama_asset):
        draw.text((text_x, text_y + 40 + (i * 20)), f"{line}", font=font, fill="black")

    # Save to memory
    img_bytes = BytesIO()
    label.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes

# Form for asset details
with st.form("asset_form"):
    nomor_asset = st.text_input("📌 Nomor Asset", placeholder="Enter Asset Number", value="INV.RHF.")
    penempatan_aset = st.text_input("📍 PENEMPATAN ASET")
    sumber = st.selectbox("🔗 Sumber", ["Invoice Fauzie", "CC Rhaya", "Invoice Futih"])
    nama_asset = st.text_input("📦 Nama Asset")
    kelompok_aset = st.selectbox("🏷️ Kelompok Aset", ["Kelompok I", "Kelompok II"])
    kepemilikan = st.selectbox("📝 Kepemilikan", ["RMU", "LDR", "RFI", "FUTIH"])
    qty = st.number_input("📊 Qty", min_value=1, step=1)
    dokumentasi = st.text_input("📷 Dokumentasi URL")
    invoice = st.text_input("🧾 Invoice URL")
    harga_perolehan = st.number_input("💰 Harga Perolehan", min_value=0, step=100000)
    tahun_beli = st.number_input("📅 Tahun Beli", min_value=2000, max_value=2100, step=1, value=2025)
    bulan_beli = st.selectbox("📆 Bulan Beli", 
                              ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                               "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    umur_ekonomis = st.number_input("📈 Umur Ekonomis (years)", min_value=1, max_value=50, step=1, value=4)
    persentase_penyusutan = st.selectbox("Persentase Penyusutan Tahunan", [25, 12.5])
    status = st.selectbox("Status Barang", ["Available", "Missing", "Unlabeled", "Others"])
    # Submit Button
    submitted = st.form_submit_button("✅ Submit")

# Generate QR Code when form is submitted
if submitted:
    if nomor_asset:

        Nilai_Penyusutan_per_Bulan =(harga_perolehan * persentase_penyusutan / 100) /12
        VALUASI_ASSET_2019 = "-"
        VALUASI_ASSET_2020 = "-"
        VALUASI_ASSET_2021 = "-"
        VALUASI_ASSET_2022 = "-"
        VALUASI_ASSET_2023 = "-"
        VALUASI_ASSET_2024 = "-"
        VALUASI_ASSET_2025 = "-"
        Nilai_Buku_2024	= "-"
        Label = True

        new_row = [
            nomor_asset, penempatan_aset, sumber, nama_asset, kelompok_aset, kepemilikan,
            qty, dokumentasi, invoice, harga_perolehan, tahun_beli, bulan_beli, umur_ekonomis,
            Nilai_Penyusutan_per_Bulan, VALUASI_ASSET_2019, VALUASI_ASSET_2020, VALUASI_ASSET_2021,
            VALUASI_ASSET_2022, VALUASI_ASSET_2023, VALUASI_ASSET_2024, VALUASI_ASSET_2025,
            Nilai_Buku_2024, status, Label
        ]
        
        # Append data to Google Sheets
        gsheet.append_data(new_row)

        label_img = generate_label(nomor_asset, kepemilikan, nama_asset)

        st.image(label_img, caption="Generated Asset Label", use_container_width=False)

        # Download Button
        st.download_button("📥 Download Label", label_img, file_name="asset_label.png", mime="image/png")
        
        st.switch_page("pages/detail_products.py")
    else:
        st.error("Nomor Asset Wajib Terisi")