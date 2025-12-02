# -----------------------------------------------------------
# invoice_extractor.py
# Streamlit/Cloud-compatible backend
# -----------------------------------------------------------

import pytesseract
import re
import pandas as pd
from pdf2image import convert_from_path
import tempfile
import os

# -----------------------------------------------------------
# Configure Tesseract path for Linux (Streamlit Cloud)
# -----------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

class ExtractInvoices:
    """
    Extracts table data from 'Stationery Invoice' PDFs.
    """

    def __init__(self):
        # No folder path needed for cloud / single uploads
        pass

    # -----------------------------------------------------------
    # STEP 1 → Convert PDF → Image → Extract Text using OCR
    # -----------------------------------------------------------
    def extract_text_from_pdf(self, pdf_path):
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page)
        return text

    # -----------------------------------------------------------
    # STEP 2 → Parse table rows from the invoice text
    # -----------------------------------------------------------
    def parse_invoice_text(self, text):
        """
        Extracts rows like:

        1   Ball Pens (Pack of 50)   20   150.0   3000.0
        2   Lunch Boxes (Set of 10)  15   800.0   12000.0
        """

        rows = []
        lines = text.split("\n")

        for line in lines:
            clean = re.sub(r"\s{2,}", " ", line).strip()

            # Row format pattern
            pattern = r"^(\d+)\s+(.*?)\s+(\d+)\s+([\d.]+)\s+([\d.]+)$"
            match = re.match(pattern, clean)

            if match:
                sno, description, qty, price, total = match.groups()
                rows.append({
                    "S.No": int(sno),
                    "Item Description": description.strip(),
                    "Quantity": int(qty),
                    "Unit Price (₹)": float(price),
                    "Total (₹)": float(total)
                })

        return rows

    # -----------------------------------------------------------
    # STEP 3 → Process a single uploaded PDF → Return DataFrame
    # -----------------------------------------------------------
    def process_single_invoice(self, uploaded_file):
        """
        uploaded_file: Streamlit uploaded file object
        """
        # Save uploaded PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        # Extract text and parse
        text = self.extract_text_from_pdf(pdf_path)
        rows = self.parse_invoice_text(text)
        df = pd.DataFrame(rows)

        # Optional: delete temporary file
        os.remove(pdf_path)

        return df
