import qrcode
from qrcode.image.pil import PilImage

# Inventory code
inventory_code = "INV.RHF.001/XI/2020"

# Create QR code object
# qr = qrcode.QRCode(
#     version=None,
#     error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
#     box_size=15,  # Bigger boxes = better scan contrast
#     border=4,
# )

# qr.add_data(inventory_code)
# qr.make(fit=True)

# # Generate image with inverted colors
# img = qr.make_image(fill_color="white", back_color="black")

# # Save image
# img.save("qr_code.png")

# print("✅ High-contrast QR Code saved as 'qr_code.png'")

from PIL import Image, ImageDraw, ImageFont
import qrcode
import textwrap
from io import BytesIO

def generate_label(nomor_asset, kepemilikan, nama_asset):
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
    label.save(output, format="PNG", dpi=(300, 300))
    output.seek(0)
    return output

with open("label.png", "wb") as f:
    f.write(generate_label("INV.RHF.025/XII/2024", "LDR", "Macbook Air 13 Inc M1 Memori 8Gb SSD 256Gb, Grey").getbuffer())

