"""Barcode-based PDF file copier."""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd

from common import FileValidator

logger = logging.getLogger("barcode_copier")


def copy_matching_pdfs(
    excel_path: str,
    pdf_folder: str,
    output_folder: str
) -> Dict[str, any]:
    """
    Copy PDFs matching barcodes from Excel file.
    
    Args:
        excel_path: Path to Excel file containing barcodes
        pdf_folder: Folder containing source PDF files
        output_folder: Destination folder for copied PDFs
        
    Returns:
        Dictionary with 'copied' count and 'not_found' list
        
    Raises:
        ValueError: If Excel file doesn't contain required column
    """
    logger.info(f"Reading barcodes from {excel_path}")
    df = pd.read_excel(excel_path)

    if "Szöveg" not in df.columns:
        raise ValueError(
            f"A kiválasztott Excel fájl nem tartalmaz 'Szöveg' nevű oszlopot. "
            f"Talált oszlopok: {list(df.columns)}"
        )

    # Extract first 10 characters as barcode
    df["Vonalkód"] = df["Szöveg"].astype(str).str[:10]
    
    # Get unique barcodes (direct iteration, no intermediate set needed)
    barcodes = df["Vonalkód"].dropna().unique()
    logger.info(f"Found {len(barcodes)} unique barcodes")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    copied_count = 0
    not_found = []

    for barcode in barcodes:
        pdf_name = f"{barcode}.pdf"
        pdf_path = os.path.join(pdf_folder, pdf_name)

        if os.path.isfile(pdf_path):
            shutil.copy2(pdf_path, os.path.join(output_folder, pdf_name))
            copied_count += 1
            logger.debug(f"Copied: {pdf_name}")
        else:
            not_found.append(barcode)
            logger.debug(f"Not found: {pdf_name}")
    
    logger.info(f"Copied {copied_count} PDFs, {len(not_found)} not found")
    
    return {
        'copied': copied_count,
        'not_found': not_found
    }