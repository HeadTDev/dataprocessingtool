import csv
import re
import os
from PyPDF2 import PdfReader
from collections import defaultdict
import pandas as pd

categories = {
    "Bérleti díj": ["Cégautóadó", "Gépjárműadó", "Finanszírozási díj", "Gépjármű kezelési díj", "Assistance szolgáltatás"],
    "Biztosítás": ["Casco biztosítás", "GAP biztosítás", "Kötelező biztosítás"],
    "Autókarbantartás": ["Abroncs szolgáltatás", "Szervizdíj  havi fix része"]
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def extract_text_from_pdf(pdf_path, start_page=2):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages[start_page-1:])

def categorize_line(line):
    for category, keywords in categories.items():
        if any(keyword in line for keyword in keywords):
            return category
    return None

def extract_amount(line):
    matches = list(re.finditer(r'(\d[\d\s\xa0\u202f]*\d)\s*HUF', line))
    if matches:
        number = ''.join(filter(str.isdigit, matches[-1].group(1)))
        return float(number[2:]) if len(number) > 2 else 0.0
    return 0.0

def process_vehicles(text, multiplier=1.27, read_data_path=None):
    if read_data_path is None:
        read_data_path = os.path.join(OUTPUT_DIR, "read_data.csv")
    pattern = re.compile(r"\n\d+\s+(\d+\/[A-Z0-9\-]+)\s+(.+?)\s+(\d[\d\s\xa0]*\d)\s+HUF")
    matches = list(pattern.finditer(text))
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
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(read_data_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Autó", "Sor", "Kategória", "Összeg"])
        writer.writerows(all_lines)
    return results

def get_license_plate(vehicle_name):
    m = re.search(r'\b([A-Z]{4}-\d{3}|[A-Z]{3}-[A-Z0-9]{3,})\b', vehicle_name)
    return m.group(1) if m else vehicle_name.split()[0]

def read_kgthely_mapping(excel_path):
    df = pd.read_excel(excel_path, dtype=str, usecols=["frsz", "Helyes ktghely"], header=1).fillna("")
    return {str(row["frsz"]).strip(): str(row["Helyes ktghely"]).strip() for _, row in df.iterrows()}

def save_to_csv_with_kgthely(data, output_path=None, kgthely_dict=None, round_amounts='No'):
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "output.csv")
    if kgthely_dict is None:
        kgthely_dict = {}
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

def run(pdf_path, excel_path):
    text = extract_text_from_pdf(pdf_path)
    vehicles = process_vehicles(text)
    kgthely = read_kgthely_mapping(excel_path)
    output_csv = os.path.join(OUTPUT_DIR, "output.csv")
    save_to_csv_with_kgthely(vehicles, output_path=output_csv, kgthely_dict=kgthely, round_amounts="Yes")