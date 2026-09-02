import os
import shutil

import pandas as pd

from app.backend.services.logging_service import get_logger

logger = get_logger("barcode_pdf")


def copy_matching_pdfs(
    excel_path, pdf_folder, output_folder, progress_callback=None, is_cancelled=None
):
    logger.info("Processing started.")
    try:
        if progress_callback:
            progress_callback("Excel beolvasása...", 0, 0)

        df = pd.read_excel(excel_path)

        if "Szöveg" not in df.columns:
            raise ValueError(
                "A kiválasztott Excel fájl nem tartalmaz 'Szöveg' nevű oszlopot."
            )

        os.makedirs(output_folder, exist_ok=True)

        df["Vonalkód"] = df["Szöveg"].astype(str).str[:10]
        barcodes = sorted(set(df["Vonalkód"].dropna()))

        copied_count = 0
        missing_barcodes = []
        total = len(barcodes)

        for index, barcode in enumerate(barcodes, start=1):
            if is_cancelled and is_cancelled():
                logger.info("Processing cancelled by user.")
                return {
                    "copied_count": copied_count,
                    "missing_count": len(missing_barcodes),
                    "missing_barcodes": missing_barcodes,
                    "cancelled": True,
                }

            if progress_callback:
                progress_callback("PDF-ek másolása...", index, total)

            pdf_name = f"{barcode}.pdf"
            pdf_path = os.path.join(pdf_folder, pdf_name)

            if os.path.isfile(pdf_path):
                shutil.copy2(pdf_path, os.path.join(output_folder, pdf_name))
                copied_count += 1
            else:
                missing_barcodes.append(str(barcode))

        logger.info(f"Processing succeeded. Copied PDFs: {copied_count}, missing: {len(missing_barcodes)}")
        return {
            "copied_count": copied_count,
            "missing_count": len(missing_barcodes),
            "missing_barcodes": missing_barcodes,
            "cancelled": False,
        }
    except Exception:
        logger.exception("Processing failed with an error.")
        raise
