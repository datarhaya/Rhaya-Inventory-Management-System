import qrcode

# Generate QR Code
inventory_code = "INV.RHF.001/XI/2020"
qr = qrcode.make(inventory_code)

# Save as image
qr.save("qr_code.png")

print("✅ QR Code saved as 'qr_code.png'")
