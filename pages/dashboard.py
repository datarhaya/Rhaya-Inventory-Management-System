import requests
import os
import json
import re

from PIL import Image
from io import BytesIO
import pathlib
from datetime import datetime

import pandas as pd
import plotly.express as px

import streamlit as st
from streamlit_cookies_controller import CookieController

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Google Drive API Setup
SCOPES = ["https://www.googleapis.com/auth/drive"]
json_data = dict(st.secrets["gdrive_auth"]["token_json"])
IMAGE_FOLDER = "downloaded_images"

controller = CookieController()

with open( pathlib.Path("app/styles.css") ) as f:
    st.markdown(f'<style>{f.read()}</style>' , unsafe_allow_html= True)

# st.markdown('<div id="my-section-{tab_id}"></div>'.format(tab_id = "rhaya-flicks-asset-management-center"), unsafe_allow_html=True)

# Markdown to make top bar invisible and has small margin
st.markdown(
    """
        <style>
                .stAppHeader {
                    background-color: rgba(255, 255, 255, 0.0);  /* Transparent background */
                    visibility: visible;  /* Ensure the header is visible */
                }

               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

data = st.session_state['data']

important_columns = ["Nomor Asset", "Nama Asset", "Tahun Beli", "Bulan Beli"]

# Optional select filters
penempatan_options = data["PENEMPATAN ASET"].dropna().unique()
selected_penempatan = st.sidebar.multiselect("📍 Penempatan Aset", penempatan_options)

sumber_options = data["Sumber"].dropna().unique()
selected_sumber = st.sidebar.multiselect("📦 Sumber", sumber_options)

kelompok_options = data["Kelompok Aset"].dropna().unique()
selected_kelompok = st.sidebar.multiselect("🗂️ Kelompok Aset", kelompok_options)

kepemilikan_options = data["Kepemilikan"].dropna().unique()
selected_kepemilikan = st.sidebar.multiselect("👥 Kepemilikan", kepemilikan_options)

# Range Tahun Beli
min_year = int(data["Tahun Beli"].min())
max_year = int(data["Tahun Beli"].max())
selected_year_range = st.sidebar.slider("📅 Tahun Beli", min_year, max_year, (min_year, max_year))
# st.write(data.sort_values("Tahun Beli"))
# Bulan in ordered list
bulan_order = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]
bulan_options = data["Bulan Beli"].dropna().unique().tolist()
bulan_sorted = [b for b in bulan_order if b in bulan_options]
selected_bulan = st.sidebar.multiselect("📆 Bulan Beli", bulan_sorted)

# Range Harga Perolehan
min_price = int(data["Harga Perolehan"].min())
max_price = int(data["Harga Perolehan"].max())
selected_price_range = st.sidebar.slider("💰 Harga Perolehan", min_price, max_price, (min_price, max_price))

# Apply filters
filtered_data = data.copy()

if selected_penempatan:
    filtered_data = filtered_data[filtered_data["PENEMPATAN ASET"].isin(selected_penempatan)]
if selected_sumber:
    filtered_data = filtered_data[filtered_data["Sumber"].isin(selected_sumber)]
if selected_kelompok:
    filtered_data = filtered_data[filtered_data["Kelompok Aset"].isin(selected_kelompok)]
if selected_kepemilikan:
    filtered_data = filtered_data[filtered_data["Kepemilikan"].isin(selected_kepemilikan)]

filtered_data = filtered_data[
    (filtered_data["Tahun Beli"] >= selected_year_range[0]) &
    (filtered_data["Tahun Beli"] <= selected_year_range[1])
]

if selected_bulan:
    filtered_data = filtered_data[filtered_data["Bulan Beli"].isin(selected_bulan)]

filtered_data = filtered_data[
    (filtered_data["Harga Perolehan"] >= selected_price_range[0]) &
    (filtered_data["Harga Perolehan"] <= selected_price_range[1])
]
# Update this line to use filtered_data instead of full data
data_filtered = filtered_data[important_columns]

# Display Table with Radio Button for Selection
# Center and align buttons closely together
# col1, col2, col3, col4, col5 = st.columns([3, 2, 0.1, 2, 3])  # Outer columns as spacers
col1, col2, col3, col4 = st.columns([2, 0.01, 2, 6])  # Outer columns as spacers

with col1:
    if st.button("📷 Scan Barcode"):
        st.switch_page("pages/scan_barcode.py")

with col3:
    if st.button("➕ Add New Item"):
        st.switch_page("pages/add_items.py")

with st.expander("See Dashboard"):
    col1, col2 = st.columns([0.4, 0.6], border=True)

    total_items = filtered_data["Qty"].sum()
    col1.metric("Total Asset", f"{total_items:,.0f} Asset")

    total_price = filtered_data["Harga Perolehan"].sum()
    col2.metric("Total Acquisition Price", f"Rp. {total_price:,.0f}")

    col1, col2 = st.columns(2, border= True)
    with col1:
        st.metric("Ownership Distribution", f"")

        ownership_percentage = (filtered_data["Kepemilikan"].value_counts(normalize=True) * 100).round(2)
        # Convert ownership data into a DataFrame
        ownership_df = pd.DataFrame({
            "Kepemilikan": ownership_percentage.index,
            "Percentage": ownership_percentage.values
        })

        # Create Pie Chart
        fig = px.pie(ownership_df, 
                    names="Kepemilikan", 
                    values="Percentage", 
                    hole=0.3)  # Creates a donut-style pie chart

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        import plotly.graph_objects as go

        # Aggregate data
        acquisition_timeline = data.groupby("Tahun Beli").agg({
            "Qty": "sum",
            "Harga Perolehan": "sum"
        }).reset_index()

        # Create figure with dual y-axis
        fig1 = go.Figure()

        # Bar chart: Jumlah Aset (left Y-axis)
        fig1.add_bar(
            x=acquisition_timeline["Tahun Beli"],
            y=acquisition_timeline["Qty"],
            name="Jumlah Aset",
            yaxis="y1"
        )

        # Line chart: Harga Perolehan (right Y-axis), scaled to juta Rp
        fig1.add_trace(go.Scatter(
            x=acquisition_timeline["Tahun Beli"],
            y=acquisition_timeline["Harga Perolehan"] / 1_000_000,  # in millions
            name="Harga Perolehan (Juta Rp)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="orange", width=3),
            marker=dict(size=6)
        ))

        # Layout with dual axes
        fig1.update_layout(
            title="Jumlah Aset dan Harga Perolehan per Tahun",
            xaxis=dict(title="Tahun Beli"),
            yaxis=dict(
                title="Jumlah Aset",
                showgrid=False
            ),
            yaxis2=dict(
                title="Harga Perolehan (Juta Rp)",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,  # Negative value moves it below the plot
            xanchor="center",
            x=0.5
        ),
            margin=dict(t=50, b=30),
            height=400
        )

        # Show chart in Streamlit
        st.plotly_chart(fig1, use_container_width=True)

# if st.button("Scan Barcode to Search Inventory"):
#     st.switch_page("pages/scan_barcode.py")

# # Display Table with Radio Button for Selection
# col1, col2 = st.columns([0.6, 0.4])
# with col1:
#     st.subheader("Inventory Details") 
# with col2:  
#     if st.button("➕ Add New Item"):
#         st.switch_page("pages/add_items.py")

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

def fetch_first_image():
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

                return image_path
            else:
                return None
            
    else: 
        return None
        
@st.dialog("Detail Asset", width='large')
def show_detail(asset):
    st.subheader(f"{asset['Nama Asset']}")

    labels = ['Nomor Asset', 'Kepemilikan', 'Harga Perolehan', 'Waktu Pembelian']
    values = [
        asset['Nomor Asset'],
        asset['Kepemilikan'],
        f"Rp. {asset['Harga Perolehan']:,.0f}",  # Format the price
        f"{asset['Bulan Beli']} {asset['Tahun Beli']:.0f}"
    ]

    for label, value in zip(labels, values):
        col1, col2 = st.columns([1, 2])
        col1.markdown(f"**{label}**")
        col2.markdown(f": {value}")

    # Show loading spinner while image loads
    with st.spinner('🔄 Loading image...'):
        image_path = fetch_first_image()  # your image URL or file path logic
        if image_path:
            try:
                if image_path.startswith("http"):
                    response = requests.get(image_path)
                    img = Image.open(BytesIO(response.content))
                else:
                    img = Image.open(image_path)
                st.image(img, caption=asset['Nama Asset'], use_container_width=True)
            except Exception as e:
                st.error(f"Failed to load image: {e}")
                st.image('assets/image not found placeholder.png', caption="Image Not Found")
        else:
            st.image('assets/image not found placeholder.png', caption="Image Not Found")

    # Page link
    st.page_link('pages/detail_products.py', label=f'More Detail', icon='🗺️')

st.markdown(' ', help="Click on left button on each row to select!")

# Show filtered table
event = st.dataframe(
    data_filtered,
    on_select='rerun',
    selection_mode='single-row'
)

if "selected_item" not in st.session_state:
    st.session_state.selected_item = None
    st.session_state.selected_asset_no = None

# Handle row selection
if len(event.selection['rows']):
    selected_row = event.selection['rows'][0]
    asset_no = data_filtered.iloc[selected_row]['Nomor Asset']

    # If asset is different from previous one, update session and show dialog
    if asset_no != st.session_state.selected_asset_no:
        st.session_state.selected_asset_no = asset_no
        # st.session_state.selected_item = data.iloc[selected_row].to_dict()
        st.session_state.selected_item = data[data['Nomor Asset'] == asset_no].iloc[0].to_dict()

        controller.set('selected_item', data[data['Nomor Asset'] == asset_no].iloc[0].to_dict())

        # Trigger dialog
        show_detail(st.session_state.selected_item)
        st.page_link('pages/detail_products.py', label=f'Goto {asset_no} Page', icon='🗺️')

elif not event.selection['rows']:
    st.write('No Selection')
    selected_row = None
    asset_no = None


