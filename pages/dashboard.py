import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import pathlib
from datetime import datetime
import pandas as pd
import plotly.express as px


with open( pathlib.Path("app/styles.css") ) as f:
    st.markdown(f'<style>{f.read()}</style>' , unsafe_allow_html= True)

st.title("Welcome to our Inventory database!")
st.write("Halaman ini dirancang untuk membantu tim Admin & Finance menemukan informasi relevan terkait item inventaris Rhaya Flicks. Segala masukan terkait dengan halaman ini dapat ditujukan pada data@rhayaflicks.com.")
st.divider()

data = st.session_state['data']

# Metrics
col1, col2, col3 = st.columns(3)

total_items = data["Qty"].sum()
total_price = data["Harga Perolehan"].sum()
ownership_percentage = (data["Kepemilikan"].value_counts(normalize=True) * 100).round(2)

col1.metric("Total Items", total_items)
col2.metric("Total Acquisition Price", f"Rp {total_price:,.2f}")
st.metric("Ownership Distribution", f"")

# Convert ownership data into a DataFrame
ownership_df = pd.DataFrame({
    "Kepemilikan": ownership_percentage.index,
    "Percentage": ownership_percentage.values
})

# Create Pie Chart
fig = px.pie(ownership_df, 
             names="Kepemilikan", 
             values="Percentage", 
            #  title="Ownership Distribution",
             hole=0.3)  # Creates a donut-style pie chart


st.plotly_chart(fig, use_container_width=True)


if st.button("Scan Barcode to Search Inventory"):
    st.switch_page("pages/scan_barcode.py")

# Display Table with Radio Button for Selection
col1, col2 = st.columns([0.6, 0.4])
with col1:
    st.subheader("Inventory Details") 
with col2:  
    if st.button("➕ Add New Item"):
        st.switch_page("pages/add_items.py")

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


