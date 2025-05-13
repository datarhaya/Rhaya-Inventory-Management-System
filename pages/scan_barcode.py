import streamlit as st
import time
from streamlit_qrcode_scanner import qrcode_scanner

if st.button("⬅️ Back" , help= "Back to Home"):
        st.switch_page("pages/dashboard.py")

st.markdown("Scan QR Code Label Inventaris", help= 'Pastikan QR Code Ada Pada Kotak dan Terlihat Jelas')
        
# Open QR Scanner
qr_code = qrcode_scanner(key="qrcode_scanner")

# Show scanning message
if not qr_code:
    st.info("📷 Scan a product QR code...")

# When QR Code is detected, find the corresponding item
if qr_code:
    st.success(f"✅ QR Code Detected: {qr_code}")
    
    # Simulate delay for better user experience
    time.sleep(0.3)

    # Get the stored dataset
    if "data" in st.session_state:
        data = st.session_state["data"]

        # Search for the matching asset number
        matched_row = data[data["Nomor Asset"] == qr_code]

        if not matched_row.empty:
            # Store selected item in session state
            st.session_state.selected_item = matched_row.iloc[0].to_dict()

            # Redirect to product detail page
            st.switch_page("pages/detail_products.py")
        else:
            st.error("❌ No matching asset found for this QR code.")
    else:
        st.error("⚠️ Data not found in session state. Make sure the data is loaded first.")
