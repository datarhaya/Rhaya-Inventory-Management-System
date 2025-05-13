import os
import re
import time
import json
import requests
import base64

from PIL import Image, ImageDraw, ImageFont
import qrcode
import textwrap
from io import BytesIO

import plotly.graph_objects as go
import numpy as np

import streamlit as st
from streamlit_cookies_controller import CookieController

from datetime import datetime
from math import floor
from dateutil.relativedelta import relativedelta
import calendar

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Drive API Setup
SCOPES = ["https://www.googleapis.com/auth/drive"]
json_data = dict(st.secrets["gdrive_auth"]["token_json"])
IMAGE_FOLDER = "downloaded_images"

controller = CookieController()
cookies = controller.getAll()

if "retry_count" not in st.session_state:
    st.session_state.retry_count = 0

if "selected_item" in st.session_state:
    data_asset = st.session_state['selected_item']
elif "selected_item" in cookies:
    data_asset = cookies['selected_item']
else:
    if st.session_state.retry_count < 3:
        st.session_state.retry_count += 1

        st.warning(f"Loading asset data... Try {st.session_state.retry_count} / 3")  # Temporary message
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("Gagal mendapatkan data asset. Kembali ke Halaman Utama")
        time.sleep(1)
        st.switch_page("pages/dashboard.py")

def get_drive_service():
    creds = None
    token_path = "token.json"
    json_path = "token.json"
    
    with open(json_path, "w") as json_file:
        json.dump(json_data, json_file)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("cred.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def extract_folder_id(drive_url):
    match = re.search(r"drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)", drive_url)
    return match.group(1) if match else None

def list_images_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get("files", [])

def download_image(service, image_id, image_name):
    """Download a single image from Google Drive."""
    image_path = os.path.join(IMAGE_FOLDER, image_name)
    
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    request = service.files().get_media(fileId=image_id)
    with open(image_path, "wb") as f:
        f.write(request.execute())

    return image_path

# Function to format numbers without decimals
def format_number(value):
    try:
        num = float(value)
        if num.is_integer():
            return f"{int(num):,}"  # Format with thousand separator (e.g., 1,000,000)
        return f"{num:,.0f}"  # Force no decimals
    except ValueError:
        return value  # Return original if not a number

def generate_label(nomor_asset, nama_asset):
    # Physical size: 60mm x 40mm → pixels at 300 DPI
    width, height = int(60 / 25.4 * 300), int(40 / 25.4 * 300)  # 708 x 472 px
    label = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(label)

    # Split into halves
    split_x = width // 2
    draw.rectangle([0, 0, split_x, height], fill="black")

    # Generate QR Code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data(nomor_asset)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="white", back_color="black").convert("RGB")

    # Resize QR
    qr_size = int(height * 0.5)
    qr_img = qr_img.resize((qr_size, qr_size))

    qr_x = (split_x - qr_size) // 2
    qr_y = int(height * 0.1)
    label.paste(qr_img, (qr_x, qr_y))

    # Logo under QR
    try:
        logo = Image.open("assets/RHF LOGO WHITE.png").convert("RGBA")
        logo_height = int(height * 0.3)
        logo_ratio = logo.width / logo.height
        logo = logo.resize((int(logo_ratio * logo_height), logo_height))
        logo_x = (split_x - logo.width) // 2
        logo_y = qr_y + qr_size + int(height * 0.04)
        label.paste(logo, (logo_x, logo_y), logo)
    except Exception as e:
        print(f"⚠️ Logo not found: {e}")

    # Load Soleil Bold font
    try:
        font = ImageFont.truetype("assets/PlusJakartaSans-ExtraBold.ttf", size=36)
        font_no_asset = ImageFont.truetype("assets/PlusJakartaSans-Bold.ttf", size=32)
    except:
        font = ImageFont.load_default()

    # Right half - asset name (top left)
    text_x = split_x + int(width * 0.02)
    text_y = int(height * 0.07)
    wrapped = textwrap.fill(nama_asset.upper(), width=14)
    draw.multiline_text((text_x, text_y), 
                        wrapped,
                        font=font,
                        fill="black", 
                        spacing=10, 
                        font_size= 26)


    # Bottom-right: nomor asset (multiline + right-aligned)
    wrapped_nomor = textwrap.wrap(nomor_asset, width=12)
    line_height = font_no_asset.getbbox("Ay")[3] + 6  # Height + spacing
    total_height = len(wrapped_nomor) * line_height

    # Bottom-right Y position (with padding)
    start_y = height - int(height * 0.1) - total_height

    for i, line in enumerate(wrapped_nomor):
        line_width = draw.textlength(line, font=font_no_asset)
        x = width - int(width * 0.04) - int(line_width)  # Right-aligned
        y = start_y + i * line_height
        draw.text((x, y), line, font=font_no_asset, fill="black")

    # Save to memory with 300 DPI
    output = BytesIO()
    # label.save(output, format="PNG", dpi=(300, 300))
    label.save(output, format="PDF", resolution=300.0)
    output.seek(0)
    return output

# Function to generate QR code separately
def generate_qr_code(nomor_asset):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(nomor_asset)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    # Save to memory
    img_bytes = BytesIO()
    qr_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes

col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.4])
with col1:
    if st.button("⬅️ Back" , help= "Back to Home"):
        st.switch_page("pages/dashboard.py")

with col2:
    if st.button("📝 Edit", help= 'Edit Items'):
        st.switch_page("pages/edit_items.py")

with col3:
    # Fetch asset details
    nomor_asset = data_asset.get("Nomor Asset", "UNKNOWN")
    nama_asset = data_asset.get("Nama Asset", "UNKNOWN")

    # Generate label and QR code
    label_img = generate_label(nomor_asset, nama_asset)
    qr_code_img = generate_qr_code(nomor_asset)

    # st.sidebar.download_button(label="📥 Download Label", data=label_img, file_name="asset_label.png", mime="image/png")
    # st.download_button(label="📥 Download",help="Download Image", data=label_img, file_name="asset_label.png", mime="image/png")
    st.sidebar.download_button(label="📥 Download Label", data=label_img, file_name="label.pdf", mime="application/pdf")
    st.download_button(label="📥 Download",help="Download Image", data=label_img, file_name="label.pdf", mime="application/pdf")

# Fetch asset details
drive_url = data_asset.get("Dokumentasi", "")

image_path = None  # Default to no image
if drive_url:
    folder_id = extract_folder_id(drive_url)

    if folder_id:
        service = get_drive_service()
        images = list_images_in_folder(service, folder_id)

        if images:
            first_image = images[0]
            image_path = download_image(service, first_image["id"], first_image["name"])

# Layout: Image on the left, key details on the right
col1, col2 = st.columns([3, 5])

import concurrent.futures

# --- Asynchronous Image Loader ---
def load_image(image_path):
    try:
        if image_path.startswith("http"):
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(image_path)
        return img
    except Exception as e:
        return f"Failed to load image: {e}"

# Trigger image loading in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    image_future = executor.submit(load_image, image_path)

with col2:
    st.write("### 📄 Asset Information")
    details_top = {
        "Nomor Asset": "Nomor Asset",
        "Nama Asset": "Nama Asset",
        "Penempatan Aset": "PENEMPATAN ASET",
        "Sumber": "Sumber",
        "Kelompok Aset": "Kelompok Aset",
        "Kepemilikan": "Kepemilikan",
        "Pembelian": f"{data_asset.get('Bulan Beli', '')} - {data_asset.get('Tahun Beli', '')}",
        "Qty": "Qty",
        "Dokumentasi": "Dokumentasi",
        "Invoice": "Invoice",
        "Status": "Status",
    }

    def is_url(value):
        return re.match(r'^https?://', value)

    def render_field(label, value):
        value = str(value)  # <-- pastikan nilai jadi string
        if re.match(r'^https?://', value):
            value_html = f'<a href="{value}" target="_blank" style="word-wrap: break-word; color: #3366cc;">{value}</a>'
        else:
            value_html = value

        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin: 0.25rem 0;">
                <div style="width: 35%; font-weight: bold;">{label}</div>
                <div style="width: 60%; word-wrap: break-word; word-break: break-word; overflow-wrap: break-word; max-width: 100%;">
                    {value_html}
                </div>
            </div>
            <hr style="margin: 4px 0 10px 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);" />
        """, unsafe_allow_html=True)

    # Use this to loop through the fields
    for label, field in details_top.items():
        value = str(data_asset.get(field, "")).strip()
        if value and value != "-":
            render_field(label, value)

with col1:
    with st.spinner("🔄 Loading image..."):
        image_result = image_future.result()
        if isinstance(image_result, Image.Image):
            buffered = BytesIO()
            image_result.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; min-height: 650px;">
                    <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; height: auto;" />
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error(image_result)
            st.image('assets/image not found placeholder.png', caption="Image Not Found")


# Below Section - Financial Information
st.write("---")
st.write("### 💰 Financial & Valuation Details")


# Helper to parse number
def parse_number(value):
    try:
        return float(str(value).replace(",", "").replace("Rp", "").strip())
    except:
        return 0.0
    
def parse_month(bulan_str):
    """Convert Indonesian month name to month number."""
    months = {
        "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
        "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
    }
    return months.get(bulan_str.lower(), 1)

def format_rupiah(value):
    return f"Rp {value:,.0f}".replace(",", ".")

# --- Extract fields
harga_perolehan = parse_number(data_asset.get("Harga Perolehan", "0"))
penyusutan_per_bulan = parse_number(data_asset.get("Nilai Penyusutan per Bulan", "0"))
umur_ekonomis = data_asset.get("Umur Ekonomis", "-")
bulan_beli = data_asset.get("Bulan Beli", "Januari")
tahun_beli = data_asset.get("Tahun Beli", None)
status = data_asset.get("Status", "-")
label = data_asset.get("Label", "-")

if tahun_beli:
    # --- Depreciation calculation
    start_month = parse_month(bulan_beli)
    start_date = datetime(tahun_beli, start_month, 1)
    today = datetime.today()

    if penyusutan_per_bulan > 0:
        total_months = floor(harga_perolehan / penyusutan_per_bulan)
        end_year = tahun_beli + (start_month - 1 + total_months) // 12
        end_month = (start_month - 1 + total_months) % 12 + 1
        end_date = datetime(end_year, end_month, 1)

        elapsed_months = max(0, (today.year - start_date.year) * 12 + (today.month - start_date.month))
        progress = min(1.0, elapsed_months / total_months)
        nilai_buku = max(0, harga_perolehan - (penyusutan_per_bulan * elapsed_months))
    else:
        total_months = 0
        progress = 0
        nilai_buku = harga_perolehan

    # --- Summary Fields

    summary_fields = {
        "Bulan Tahun Beli": f"{bulan_beli} {tahun_beli}",
        "Harga Perolehan": format_rupiah(harga_perolehan),
        "Nilai Buku Sekarang": format_rupiah(nilai_buku),
        "Umur Ekonomis": f"{umur_ekonomis} tahun",
        "Nilai Penyusutan per Bulan": format_rupiah(penyusutan_per_bulan)
    }

    for label, value in summary_fields.items():
        render_field(label, value)

    # --- Progress bar
    if penyusutan_per_bulan > 0:
        remaining_months = max(0, (end_date.year - today.year) * 12 + (end_date.month - today.month))

        st.markdown(
            f"📉 Aset akan **habis nilai** pada **{calendar.month_name[end_month]} {end_year}** "
            f"setelah {total_months} bulan. "
            f"<br>🕒 Sisa waktu: **{remaining_months} bulan** dari sekarang.",
            unsafe_allow_html=True
        )
        st.progress(progress, text=f"{int(progress * 100)}% penyusutan")
    else:
        st.warning("Nilai penyusutan per bulan tidak valid atau nol.")

with st.expander("Detail Penyusutan"):
    # --- Financial calculations for yearly summary
    def calculate_yearly_depreciation(harga_perolehan, penyusutan_per_bulan, total_months):
        depreciation_per_year = penyusutan_per_bulan * 12
        nilai_buku_tahunan = []
        total_depreciation_tahunan = []

        for year in range(total_months // 12 + 1):
            depreciation_this_year = min(depreciation_per_year * (year + 1), harga_perolehan)
            remaining_value = harga_perolehan - depreciation_this_year
            
            # Stop calculation if the value is less than or equal to 0
            if remaining_value <= 0:
                break
            
            nilai_buku_tahunan.append(remaining_value)
            total_depreciation_tahunan.append(depreciation_this_year)

        return nilai_buku_tahunan, total_depreciation_tahunan

    # Calculate yearly values
    if tahun_beli and penyusutan_per_bulan > 0:
        nilai_buku_tahunan, total_depreciation_tahunan = calculate_yearly_depreciation(
            harga_perolehan, penyusutan_per_bulan, total_months
        )

        # --- Plotly chart setup
        years = np.arange(tahun_beli, tahun_beli + len(nilai_buku_tahunan))

        # Create a line chart for Nilai Buku Tahunan
        line_trace = go.Scatter(
            x=years, y=nilai_buku_tahunan, mode='lines+markers', name='Nilai Buku Tahunan',
            line=dict(color='#0D2A52')
        )

        # Create a bar chart for Total Penyusutan Tahunan
        bar_trace = go.Bar(
            x=years, y=total_depreciation_tahunan, name='Total Penyusutan Tahunan',
            marker=dict(color='#48A6A7')
        )

        # Create the layout for the chart
        layout = go.Layout(
            title='Perkembangan Nilai Buku dan Penyusutan Tahunan',
            xaxis=dict(title='Tahun'),
            yaxis=dict(title='Nilai (Rp)'),
            barmode='group',
            template='plotly_white'
        )

        # Combine both charts
        fig = go.Figure(data=[line_trace, bar_trace], layout=layout)

        # Display the chart with Streamlit
        st.plotly_chart(fig)

    else:
        st.warning("Perhitungan nilai buku dan penyusutan tahunan gagal karena data tidak lengkap.")



st.write("---")
st.write("### Others Details")
st.write("Disini akan diisikan detail kondisi barang, serial number, tipe lengkap dan lain lain")