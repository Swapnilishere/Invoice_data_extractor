# ----------------------------------------------------------- 
# invoice_extractor.py
# Streamlit/Cloud-compatible backend
# Handles digital PDFs + scanned PDFs
# -----------------------------------------------------------

import re
import pandas as pd
import tempfile
import os
import streamlit as st

# PDF processing
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

# -----------------------------------------------------------
# Configure Tesseract path for Streamlit Cloud (if OCR needed)
# -----------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


class ExtractInvoices:
    """
    Extracts table data from 'Stationery Invoice' PDFs.
    """

    def __init__(self):
        pass

    # -----------------------------------------------------------
    # STEP 1 → Extract text from PDF (digital or scanned)
    # -----------------------------------------------------------
    def extract_text_from_pdf(self, pdf_path):
        """
        First tries pdfplumber (works for digital PDFs).
        If no text found, falls back to OCR using pdf2image + pytesseract.
        """
        text = ""

        # --- Try pdfplumber first ---
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            st.warning(f"pdfplumber failed: {e}")

        # --- Fallback to OCR if no text found ---
        if not text.strip():
            try:
                pages = convert_from_path(pdf_path, dpi=300, poppler_path="/usr/bin")
                for page in pages:
                    text += pytesseract.image_to_string(page) + "\n"
            except Exception as e:
                st.error(f"OCR failed: {e}")
                return ""

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
            pattern = r"^(\d+)\s+(.*?)\s+(\d+)\s+([\d.,]+)\s+([\d.,]+)$"
            match = re.match(pattern, clean)

            if match:
                sno, description, qty, price, total = match.groups()
                # Remove commas from numbers if present
                price = price.replace(",", "")
                total = total.replace(",", "")
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
    # Rewind file pointer to start
    uploaded_file.seek(0)

    # Save uploaded PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = tmp.name

    print(f"[DEBUG] PDF saved at: {pdf_path}, size: {os.path.getsize(pdf_path)} bytes")

    if os.path.getsize(pdf_path) == 0:
        st.error("Uploaded PDF is empty.")
        return pd.DataFrame()

    # Extract text and parse
    text = self.extract_text_from_pdf(pdf_path)
    rows = self.parse_invoice_text(text)
    df = pd.DataFrame(rows)

    # Optional: delete temporary file
    os.remove(pdf_path)

    if df.empty:
        st.error("❌ No table data detected. Check the invoice format.")

    return df
