import streamlit as st
import os
import re
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from PIL import Image

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


# Streamlit App
st.title("📦 Asset Details")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⬅️ Back to Home"):
        st.switch_page("pages/dashboard.py")

with col2:
    if st.button("Edit Items"):
        st.switch_page("pages/edit_items.py")

drive_url = st.session_state.selected_item["Dokumentasi"]

if drive_url:
    service = get_drive_service()
    folder_id = extract_folder_id(drive_url)

    if folder_id:
        images = list_images_in_folder(service, folder_id)

        if images:
            # Download only the first image
            first_image = images[0]
            first_image_path = download_image(service, first_image["id"], first_image["name"])

            # Layout: Image on the left, key details on the right
            col1, col2 = st.columns([3, 5])

            with col1:
                st.image(first_image_path, caption="📷 Asset Image", use_container_width=True)

            with col2:
                st.write("### 📄 Asset Information")
                # Upper-right fields
                details_top = {
                    "🆔 Nomor Asset": "Nomor Asset",
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

                # Display in col2 (Right Side)
                with col2:
                    for label, field in details_top.items():
                        value = str(st.session_state.selected_item.get(field, "")).strip()

                        # Show only non-empty values
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
                # Apply formatting for numeric fields
                if field in ["Harga Perolehan", "Umur Ekonomis", "Nilai Penyusutan per Bulan",
                            "VALUASI ASSET 2019", "VALUASI ASSET 2020", "VALUASI ASSET 2021",
                            "VALUASI ASSET 2022", "VALUASI ASSET 2023", "VALUASI ASSET 2024",
                            "VALUASI ASSET 2025", "Nilai Buku 2024"]:
                    value = format_number(value)

                # Only display non-empty values
                if value and value != "-":
                    st.write(f"**{label}:** {value}")
     
        else:
            st.warning("⚠️ No images found in the folder.")
    else:
        st.error("❌ Invalid Google Drive URL.")
else:
    st.warning("⚠️ Please enter a valid Google Drive folder URL.")
