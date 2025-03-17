import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import pathlib
from datetime import datetime
import pandas as pd

with open( pathlib.Path("app/styles.css") ) as f:
    st.markdown(f'<style>{f.read()}</style>' , unsafe_allow_html= True)

st.title("Welcome to our internal database!")
st.write("Halaman ini dirancang untuk membantu seluruh tim menemukan informasi relevan terkait proyek film yang ditangani oleh Rhaya Flicks. Untuk mengakses berbagai marketing items serta informasi film, kamu bisa menekan tombol “see more”. Segala masukan terkait dengan halaman ini dapat ditujukan pada data@rhayaflicks.com.")
st.divider()

data = st.session_state['data']

# Metrics
col1, col2, col3 = st.columns(3)

total_items = data["Qty"].sum()
total_price = data["Harga Perolehan"].sum()
ownership_percentage = (data["Kepemilikan"].value_counts(normalize=True) * 100).round(2)

col1.metric("Total Items", total_items)
col2.metric("Total Acquisition Price", f"Rp {total_price:,.2f}")
col3.metric("Ownership Distribution", f"See Table Below")

# Ownership Percentage Table
st.subheader("Ownership Percentage")
st.dataframe(ownership_percentage)

# Add Item Button
if st.button("➕ Add New Item"):
    st.switch_page("pages/add_items.py")

# Display Table with Radio Button for Selection
st.subheader("Inventory Details")
important_columns = ["Nomor Asset", "Nama Asset", "Tahun Beli", "Bulan Beli"]
data_filtered = data[important_columns]


# Show filtered table
event = st.dataframe(
    data_filtered,
    on_select='rerun',
    selection_mode='single-row'
)

if len(event.selection['rows']):
    selected_row = event.selection['rows'][0]
    asset_no = data_filtered.iloc[selected_row]['Nomor Asset']
    
    st.session_state.selected_item = data.iloc[selected_row].to_dict()
    st.page_link('pages/detail_products.py', label=f'Goto {asset_no} Page', icon='🗺️')


