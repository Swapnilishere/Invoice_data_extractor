# -----------------------------------------------------------
# app.py
# Streamlit PDF Invoice Extractor (Cloud-Ready)
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
import io
import tempfile
from invoice_extractor import ExtractInvoices

# ---------------------------------------------
# Streamlit Page Settings
# ---------------------------------------------
st.set_page_config(
    page_title="Invoice Table Extractor",
    page_icon="🧾",
    layout="centered"
)

st.title("🧾 Invoice Table Extractor")
st.write("Upload your Stationery Invoice PDF and extract table data.")

# ---------------------------------------------
# File Upload
# ---------------------------------------------
uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

    # Temporarily save uploaded PDF in a safe temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        temp_pdf_path = tmp.name

    # ---------------------------------------------
    # Extract Button
    # ---------------------------------------------
    if st.button("Extract Table Data"):
        st.info("Extracting data... Please wait.")

        # Create Extractor Object (folder_path not used)
        extractor = ExtractInvoices()

        # Extract data from the uploaded file
        df = extractor.process_single_invoice(uploaded_file)

        if df.empty:
            st.error("❌ No table data detected. Check the invoice format.")
        else:
            st.success("✔ Extraction Successful!")

            st.subheader("📄 Extracted Table")
            st.dataframe(df, use_container_width=True)

            # ---------------------------------------------
            # Download Excel (in-memory)
            # ---------------------------------------------
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            st.download_button(
                label="⬇ Download Excel",
                data=excel_buffer,
                file_name="extracted_invoice.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ---------------------------------------------
            # Download CSV (in-memory)
            # ---------------------------------------------
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="⬇ Download CSV",
                data=csv_buffer.getvalue(),
                file_name="extracted_invoice.csv",
                mime="text/csv"
            )

# ---------------------------------------------
# Footer
# ---------------------------------------------
st.write("---")
st.caption("Built with ❤️ using Python, Streamlit & Tesseract OCR.")
