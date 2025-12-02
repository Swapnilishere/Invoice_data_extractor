# ----------------------------------------------------------- 
# invoice_extractor.py
# Streamlit/Cloud-compatible backend with PDF validation
# -----------------------------------------------------------

import pytesseract
import re
import pandas as pd
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
import tempfile
import os
import streamlit as st

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
        """
        Converts PDF pages to images and extracts text using Tesseract OCR.
        Added poppler_path for Streamlit Cloud compatibility.
        """

        # Check if PDF is empty
        if os.path.getsize(pdf_path) == 0:
            st.error("❌ Uploaded PDF is empty.")
            return ""

        try:
            pages = convert_from_path(pdf_path, dpi=300, poppler_path="/usr/bin")
        except PDFPageCountError:
            st.error("❌ Unable to read PDF. It may be corrupted or empty.")
            return ""
        except Exception as e:
            st.error(f"❌ PDF conversion failed: {str(e)}")
            return ""

        text = ""
        for page in pages:
            try:
                text += pytesseract.image_to_string(page)
            except Exception as e:
                st.error(f"❌ OCR failed on a page: {str(e)}")
                continue

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
        if not text:
            return rows

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
        if not text:
            # PDF invalid or OCR failed
            os.remove(pdf_path)
            return pd.DataFrame()

        rows = self.parse_invoice_text(text)
        df = pd.DataFrame(rows)

        # Optional: delete temporary file
        os.remove(pdf_path)

        return df

