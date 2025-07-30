import os
import shutil
import pandas as pd

def copy_matching_pdfs(excel_path, pdf_folder, output_folder):
    df = pd.read_excel(excel_path)

    if "Szöveg" not in df.columns:
        raise ValueError("A kiválasztott Excel fájl nem tartalmaz 'Szöveg' nevű oszlopot.")

    df["Vonalkód"] = df["Szöveg"].astype(str).str[:10]
    barcodes = set(df["Vonalkód"].dropna())

    copied_count = 0

    for barcode in barcodes:
        pdf_name = f"{barcode}.pdf"
        pdf_path = os.path.join(pdf_folder, pdf_name)

        if os.path.isfile(pdf_path):
            shutil.copy2(pdf_path, os.path.join(output_folder, pdf_name))
            copied_count += 1

    return copied_count