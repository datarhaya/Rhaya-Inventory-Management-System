# import EAN13 from barcode module 
import barcode
from barcode.writer import ImageWriter 
import re

inventory_code = "INV.RHF.001/XI/2020"
code39 = barcode.get_barcode_class("code39")
barcode_instance = code39(inventory_code, writer=ImageWriter())

barcode_instance.save("new_code1")
