"""Invoice data extraction from SAP export files."""

import re
import logging
from typing import List, Dict
import chardet

from common import parse_hungarian_number, format_hungarian_number

logger = logging.getLogger("cofanet_help")

# Pre-compiled regex patterns
NEV_PATTERN = re.compile(r'^\s*Név\s+(.*)$')
SZAMLA_PATTERN = re.compile(r'^\s*\*\*\s*Számla\s+(\d+)')
AMOUNTS_PATTERN = re.compile(r'([\d\.,]+)\s+(HUF|EUR)\s+([\d\.,]+)\s+(HUF|EUR)\s*$')


def detect_encoding(filename: str) -> str:
    """
    Detect file encoding using chardet.
    
    Args:
        filename: Path to file
        
    Returns:
        Detected encoding name
    """
    with open(filename, 'rb') as f:
        raw_data = f.read(10000)  # Read first 10KB
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'


def extract_invoice_summary(filename: str) -> List[Dict[str, str]]:
    """
    Extract invoice summary from SAP export file.
    
    Extracts 'Név' and '** Számla' lines, parsing amounts from line endings.
    Consolidates 'praktiker' companies under 'Praktiker Kft.'.
    
    Args:
        filename: Path to SAP export file
        
    Returns:
        List of invoice summary dictionaries
    """
    logger.info(f"Extracting invoice summary from {filename}")
    
    # Try to detect encoding first
    try:
        encoding = detect_encoding(filename)
        logger.info(f"Detected encoding: {encoding}")
    except Exception:
        encoding = 'utf-16'  # Default fallback
    
    encodings = [encoding, 'utf-16', 'utf-8']
    results = []
    cegnev = None
    
    for enc in encodings:
        try:
            with open(filename, encoding=enc) as f:
                for line in f:
                    line = line.rstrip('\n')
                    
                    # Check for company name
                    m_nev = NEV_PATTERN.match(line)
                    if m_nev:
                        cegnev = m_nev.group(1).strip()
                        continue
                    
                    # Check for invoice line
                    m_szamla = SZAMLA_PATTERN.match(line)
                    if m_szamla:
                        m_amounts = AMOUNTS_PATTERN.search(line.replace('\t', ' '))
                        if m_amounts:
                            osszeg_bp = m_amounts.group(1).strip()
                            bp_penznem = m_amounts.group(2).strip()
                            osszeg_sp = m_amounts.group(3).strip()
                            sp_penznem = m_amounts.group(4).strip()
                        else:
                            osszeg_bp = bp_penznem = osszeg_sp = sp_penznem = ""
                        
                        results.append({
                            "cegnev": cegnev if cegnev else "",
                            "osszeg_bp": osszeg_bp,
                            "bp_penznem": bp_penznem,
                            "osszeg_sp": osszeg_sp,
                            "sp_penznem": sp_penznem
                        })
            
            logger.info(f"Successfully parsed with encoding {enc}, found {len(results)} invoices")
            break
            
        except Exception as e:
            logger.debug(f"Failed to parse with encoding {enc}: {e}")
            continue

    # PRAKTIKER consolidation
    logger.info("Consolidating Praktiker entries")
    praktiker_key = "Praktiker Kft."
    summarized = {}
    
    for row in results:
        company = row["cegnev"]
        is_praktiker = "praktiker" in company.lower()
        key = praktiker_key if is_praktiker else company
        
        if key not in summarized:
            summarized[key] = {
                "cegnev": key,
                "osszeg_bp": 0.0,
                "bp_penznem": row["bp_penznem"],
                "osszeg_sp": 0.0,
                "sp_penznem": row["sp_penznem"]
            }
        
        # Use common utility for parsing Hungarian numbers
        try:
            summarized[key]["osszeg_bp"] += parse_hungarian_number(row["osszeg_bp"])
        except ValueError:
            pass
        
        try:
            summarized[key]["osszeg_sp"] += parse_hungarian_number(row["osszeg_sp"])
        except ValueError:
            pass
        
        # Update currency if empty
        if not summarized[key]["bp_penznem"]:
            summarized[key]["bp_penznem"] = row["bp_penznem"]
        if not summarized[key]["sp_penznem"]:
            summarized[key]["sp_penznem"] = row["sp_penznem"]
    
    # Format back to Hungarian format
    output_rows = []
    for data in summarized.values():
        output_rows.append({
            "cegnev": data["cegnev"],
            "osszeg_bp": format_hungarian_number(data["osszeg_bp"]),
            "bp_penznem": data["bp_penznem"],
            "osszeg_sp": format_hungarian_number(data["osszeg_sp"]),
            "sp_penznem": data["sp_penznem"]
        })
    
    # Sort by company name
    output_rows.sort(key=lambda x: x["cegnev"].lower())
    
    logger.info(f"Consolidated to {len(output_rows)} unique companies")
    return output_rows

def write_vevok_csv(results: List[Dict[str, str]], output_path: str) -> None:
    """
    Write customer results to CSV file.
    
    Args:
        results: List of customer dictionaries
        output_path: Output CSV file path
    """
    import csv
    
    logger.info(f"Writing {len(results)} results to {output_path}")
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "cegnev", "osszeg_bp", "bp_penznem", "osszeg_sp", "sp_penznem"
        ])
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"CSV file written successfully")