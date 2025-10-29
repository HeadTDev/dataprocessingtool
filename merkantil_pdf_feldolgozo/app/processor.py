"""Vehicle cost processor for Merkantil PDF files."""

import csv
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PyPDF2 import PdfReader
from collections import defaultdict
import pandas as pd
import logging

from common import Config, setup_logging, ensure_output_dir

logger = setup_logging(module_name="merkantil_processor")

# Pre-compiled regex patterns (performance improvement)
VEHICLE_PATTERN = re.compile(r"\n\d+\s+(\d+\/[A-Z0-9\-]+)\s+(.+?)\s+(\d[\d\s\xa0]*\d)\s+HUF")
AMOUNT_PATTERN = re.compile(r'(\d[\d\s\xa0\u202f]*\d)\s*HUF')
LICENSE_PLATE_PATTERN = re.compile(r'\b([A-Z]{4}-\d{3}|[A-Z]{3}-[A-Z0-9]{3,})\b')

# Category keywords
CATEGORIES = {
    "Bérleti díj": ["Cégautóadó", "Gépjárműadó", "Finanszírozási díj", "Gépjármű kezelési díj", "Assistance szolgáltatás"],
    "Biztosítás": ["Casco biztosítás", "GAP biztosítás", "Kötelező biztosítás"],
    "Autókarbantartás": ["Abroncs szolgáltatás", "Szervizdíj  havi fix része"]
}

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"

def extract_text_from_pdf(pdf_path: str, start_page: int = 2) -> str:
    """
    Extract text from PDF starting at specified page.
    
    Args:
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        
    Returns:
        Extracted text as string
    """
    logger.info(f"Extracting text from PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages[start_page-1:])
    logger.debug(f"Extracted {len(text)} characters from PDF")
    return text

def categorize_line(line: str) -> Optional[str]:
    """
    Categorize a line based on keywords.
    
    Args:
        line: Line of text to categorize
        
    Returns:
        Category name or None if no match
    """
    for category, keywords in CATEGORIES.items():
        if any(keyword in line for keyword in keywords):
            return category
    return None

def extract_amount(line: str) -> float:
    """
    Extract amount from a line containing HUF values.
    
    Args:
        line: Line of text containing amount
        
    Returns:
        Extracted amount as float, or 0.0 if not found
    """
    matches = list(AMOUNT_PATTERN.finditer(line))
    if matches:
        number = ''.join(filter(str.isdigit, matches[-1].group(1)))
        return float(number[2:]) if len(number) > 2 else 0.0
    return 0.0

def process_vehicles(
    text: str,
    multiplier: float = None,
    read_data_path: Optional[Path] = None
) -> List[Tuple[str, Dict[str, float]]]:
    """
    Process vehicle data from PDF text.
    
    Args:
        text: Extracted PDF text
        multiplier: Multiplier to apply to amounts (default from Config)
        read_data_path: Path to save detailed data CSV
        
    Returns:
        List of (vehicle_name, categorized_amounts) tuples
    """
    if multiplier is None:
        multiplier = Config.DEFAULT_MULTIPLIER
    
    if read_data_path is None:
        read_data_path = OUTPUT_DIR / "read_data.csv"
    
    logger.info(f"Processing vehicles with multiplier {multiplier}")
    matches = list(VEHICLE_PATTERN.finditer(text))
    logger.info(f"Found {len(matches)} vehicles")
    
    results, all_lines = [], []
    for idx, m in enumerate(matches):
        vehicle_name = f"{m.group(1)} {m.group(2)}".strip()
        block = text[m.end():matches[idx+1].start() if idx+1 < len(matches) else len(text)]
        grouped = defaultdict(float)
        
        for line in block.splitlines():
            line = line.strip()
            category = categorize_line(line)
            amount = extract_amount(line) if category else ""
            all_lines.append([vehicle_name, line, category or "", amount or ""])
            if category and isinstance(amount, (int, float)):
                grouped[category] += amount
        
        results.append((vehicle_name, {cat: round(val * multiplier, 2) for cat, val in grouped.items()}))
    
    # Save detailed data
    ensure_output_dir(BASE_DIR)
    with open(read_data_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Autó", "Sor", "Kategória", "Összeg"])
        writer.writerows(all_lines)
    
    logger.info(f"Saved detailed data to {read_data_path}")
    return results

def get_license_plate(vehicle_name: str) -> str:
    """
    Extract license plate from vehicle name.
    
    Args:
        vehicle_name: Full vehicle name string
        
    Returns:
        License plate or first word if not found
    """
    m = LICENSE_PLATE_PATTERN.search(vehicle_name)
    return m.group(1) if m else vehicle_name.split()[0]

def read_kgthely_mapping(excel_path: str) -> Dict[str, str]:
    """
    Read mapping from Excel file.
    
    Args:
        excel_path: Path to Excel file with mapping
        
    Returns:
        Dictionary mapping frsz to ktghely
    """
    logger.info(f"Reading ktghely mapping from {excel_path}")
    df = pd.read_excel(excel_path, dtype=str, usecols=["frsz", "Helyes ktghely"], header=1).fillna("")
    mapping = {str(row["frsz"]).strip(): str(row["Helyes ktghely"]).strip() for _, row in df.iterrows()}
    logger.info(f"Loaded {len(mapping)} mappings")
    return mapping

def save_to_csv_with_kgthely(
    data: List[Tuple[str, Dict[str, float]]],
    output_path: Optional[Path] = None,
    kgthely_dict: Optional[Dict[str, str]] = None,
    round_amounts: str = 'No'
) -> None:
    """
    Save processed data to CSV with ktghely information.
    
    Args:
        data: List of (vehicle_name, categorized_amounts) tuples
        output_path: Output CSV path
        kgthely_dict: Mapping of license plates to ktghely
        round_amounts: 'Yes' to round amounts, 'No' for decimal precision
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "output.csv"
    if kgthely_dict is None:
        kgthely_dict = {}
    
    logger.info(f"Saving output to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Autó", "Kategória", "Összeg HUF (ÁFÁ-val)", "Helyes ktghely"])
        
        for vehicle, cats in data:
            plate = get_license_plate(vehicle)
            helyes = kgthely_dict.get(plate, "")
            
            for i, cat in enumerate(["Bérleti díj", "Biztosítás", "Autókarbantartás"]):
                value = cats.get(cat, 0.0)
                val = f"{round(value):,}".replace(",", ".") if round_amounts.lower() == 'yes' else f"{value:,.2f}".replace(",", ".")
                writer.writerow([vehicle if i == 0 else "", cat, val, helyes if i == 0 else ""])
    
    logger.info(f"Saved {len(data)} vehicles to CSV")

def run(pdf_path: str, excel_path: str) -> None:
    """
    Main processing function.
    
    Args:
        pdf_path: Path to PDF file
        excel_path: Path to Excel file with ktghely mapping
    """
    logger.info(f"Starting processing: PDF={pdf_path}, Excel={excel_path}")
    
    text = extract_text_from_pdf(pdf_path)
    vehicles = process_vehicles(text)
    kgthely = read_kgthely_mapping(excel_path)
    
    output_csv = OUTPUT_DIR / "output.csv"
    save_to_csv_with_kgthely(vehicles, output_path=output_csv, kgthely_dict=kgthely, round_amounts="Yes")
    
    logger.info("Processing completed successfully")