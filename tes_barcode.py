import qrcode
from qrcode.image.pil import PilImage

# Inventory code
inventory_code = "INV.RHF.001/XI/2020"

# Create QR code object
qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
    box_size=15,  # Bigger boxes = better scan contrast
    border=4,
)

qr.add_data(inventory_code)
qr.make(fit=True)

# Generate image with inverted colors
img = qr.make_image(fill_color="white", back_color="black")

# Save image
img.save("qr_code.png")

print("✅ High-contrast QR Code saved as 'qr_code.png'")
