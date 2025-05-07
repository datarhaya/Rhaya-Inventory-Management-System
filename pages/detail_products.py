import streamlit as st
import os
import re
import json
import textwrap
import qrcode
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Drive API Setup
SCOPES = ["https://www.googleapis.com/auth/drive"]
json_data = dict(st.secrets["gdrive_auth"]["token_json"])
IMAGE_FOLDER = "downloaded_images"

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
    
# Function to generate asset label
def generate_label(nomor_asset, kepemilikan, nama_asset):
    label_width, label_height = 227, 151  # 60mm x 40mm at 96 DPI

    # Create blank label
    label = Image.new("RGB", (label_width, label_height), "white")
    draw = ImageDraw.Draw(label)

    # Generate QR Code
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(nomor_asset)
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")

    # Resize QR Code
    qr_size = 90  
    qr_img = qr_img.resize((qr_size, qr_size))

    # Load font
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    # Position QR Code
    qr_x = 5
    qr_y = (label_height - qr_size) // 2
    label.paste(qr_img, (qr_x, qr_y))

    # Text positions
    text_x = qr_x + qr_size + 5  
    text_y = qr_y + 7

    # Wrap text for Nama Asset (Max 2 Lines)
    max_width = label_width - text_x - 5  
    wrapped_lines = textwrap.wrap(nama_asset, width=20)  
    if len(wrapped_lines) > 2:
        wrapped_nama_asset = wrapped_lines[:2]
        wrapped_nama_asset[-1] += "..."  # Add ellipses if exceeded
    else:
        wrapped_nama_asset = wrapped_lines

    # Draw text
    draw.text((text_x, text_y), f"{nomor_asset}", font=font, fill="black")  # Nomor Asset
    draw.text((text_x, text_y + 20), f"{kepemilikan}", font=font, fill="black")  # Kepemilikan
    
    for i, line in enumerate(wrapped_nama_asset):
        draw.text((text_x, text_y + 40 + (i * 20)), f"{line}", font=font, fill="black")

    # Save to memory
    img_bytes = BytesIO()
    label.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return img_bytes

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

# Streamlit App
# st.title("📦 Asset Details")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ Back to Home"):
        st.switch_page("pages/dashboard.py")

with col2:
    if st.button("Edit Items"):
        st.switch_page("pages/edit_items.py")

with col3:
    # Fetch asset details
    nomor_asset = st.session_state.selected_item.get("Nomor Asset", "UNKNOWN")
    kepemilikan = st.session_state.selected_item.get("Kepemilikan", "UNKNOWN")
    nama_asset = st.session_state.selected_item.get("Nama Asset", "UNKNOWN")

    # Generate label and QR code
    label_img = generate_label(nomor_asset, kepemilikan, nama_asset)
    qr_code_img = generate_qr_code(nomor_asset)

    # # Display label image
    # st.image(label_img, caption="Generated Asset Label", use_container_width=False)

    st.download_button(label="📥 Download Label", data=label_img, file_name="asset_label.png", mime="image/png")

# Fetch asset details
drive_url = st.session_state.selected_item.get("Dokumentasi", "")

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

with col1:
    # Show loading spinner while image loads
    with st.spinner('🔄 Loading image...'):
        if image_path:
            try:
                if image_path.startswith("http"):
                    response = requests.get(image_path)
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(image_path)
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to load image: {e}")
                st.image('assets/image not found placeholder.png', caption="Image Not Found")
        else:
            st.image('assets/image not found placeholder.png', caption="Image Not Found")

    # if image_path:
    #     st.image(image_path, use_container_width=True)
    # else:
    #     st.image('assets/image not found placeholder.png', caption="Image Not Found")

with col2:
    st.write("### 📄 Asset Information")
    details_top = {
        "🆔 Nomor Asset": "Nomor Asset",
        "📍 Nama Asset": "Nama Asset",
        "📍 Penempatan Aset": "PENEMPATAN ASET",
        "🔗 Sumber": "Sumber",
        "🏷️ Kelompok Aset": "Kelompok Aset",
        "📝 Kepemilikan": "Kepemilikan",
        "📆 Pembelian": f"{st.session_state.selected_item.get('Bulan Beli', '')} - {st.session_state.selected_item.get('Tahun Beli', '')}",
        "📊 Qty": "Qty",
        "🖼️ Dokumentasi": "Dokumentasi",
        "🧾 Invoice": "Invoice",
        "📌 Status": "Status",
    }

    for label, field in details_top.items():
        value = str(st.session_state.selected_item.get(field, "")).strip()
        if value and value != "-":
            st.write(f"**{label}:** {value}")

# Below Section - Financial Information
st.write("---")
st.write("### 💰 Financial & Valuation Details")

details_bottom = {
    "💰 Harga Perolehan": "Harga Perolehan",
    "📆 Pembelian": f"{st.session_state.selected_item.get('Bulan Beli', '')} - {st.session_state.selected_item.get('Tahun Beli', '')}",
    "📈 Umur Ekonomis (years)": "Umur Ekonomis",
    "📉 Nilai Penyusutan per Bulan": "Nilai Penyusutan per Bulan",
    "💎 Valuasi Asset 2019": "VALUASI ASSET 2019",
    "💎 Valuasi Asset 2020": "VALUASI ASSET 2020",
    "💎 Valuasi Asset 2021": "VALUASI ASSET 2021",
    "💎 Valuasi Asset 2022": "VALUASI ASSET 2022",
    "💎 Valuasi Asset 2023": "VALUASI ASSET 2023",
    "💎 Valuasi Asset 2024": "VALUASI ASSET 2024",
    "💎 Valuasi Asset 2025": "VALUASI ASSET 2025",
    "🏦 Nilai Buku 2024": "Nilai Buku 2024",
    "📌 Status": "Status",
    "🔖 Label": "Label"
}

for label, field in details_bottom.items():
    value = str(st.session_state.selected_item.get(field, "")).strip()
    if field in ["Harga Perolehan", "Umur Ekonomis", "Nilai Penyusutan per Bulan",
                 "VALUASI ASSET 2019", "VALUASI ASSET 2020", "VALUASI ASSET 2021",
                 "VALUASI ASSET 2022", "VALUASI ASSET 2023", "VALUASI ASSET 2024",
                 "VALUASI ASSET 2025", "Nilai Buku 2024"]:
        value = format_number(value)

    if value and value != "-":
        st.write(f"**{label}:** {value}")
