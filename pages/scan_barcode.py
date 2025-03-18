import streamlit as st
import time
from streamlit_qrcode_scanner import qrcode_scanner

# Set page title
st.title("🔍 Search Products")

# Open QR Scanner
qr_code = qrcode_scanner(key="qrcode_scanner")

# Show scanning message
if not qr_code:
    st.info("📷 Scan a product QR code...")

# When QR Code is detected, redirect to detail page
if qr_code:
    st.success(f"✅ QR Code Detected: {qr_code}")
    
    # Simulate delay for better user experience
    time.sleep(1.5)
    
    # Redirect to product detail page
    st.session_state["barcode"] = qr_code
    st.switch_page("pages/detail_products.py")
