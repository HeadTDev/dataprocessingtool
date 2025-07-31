import os
import csv
import sys
import unicodedata
import re
from difflib import SequenceMatcher
from openpyxl import load_workbook
from openpyxl.styles import numbers

def normalize_name(name):
    if not name:
        return ""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    name = name.lower()
    name = re.sub(
        r'\b(kft\.?|zrt\.?|bt\.?|gmbh|ltd\.?|nyrt\.?|rt\.?|b\.v\.?|s\.a\.?|s\.r\.l\.?|se|ev|sas|korlatolt felelossegu tarsasag|szolgaltato|kereskedelmi|beteti tarsasag|nonprofit)\b',
        '', name)
    name = re.sub(r'[^a-z0-9]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def best_fuzzy_match(vevo_name, coface_names, threshold=0.80):
    norm_vevo = normalize_name(vevo_name)
    best_idx, best_score = None, 0.0
    for idx, name in enumerate(coface_names):
        norm_coface = normalize_name(name)
        score = SequenceMatcher(None, norm_vevo, norm_coface).ratio()
        words_v = set(norm_vevo.split())
        words_c = set(norm_coface.split())
        word_score = len(words_v & words_c) / max(1, len(words_v | words_c))
        total_score = max(score, word_score)
        if total_score > best_score:
            best_score = total_score
            best_idx = idx
    if best_score >= threshold:
        return best_idx
    return None

def format_amount(amount_str):
    """
    Formázza az összeget helyes számformátumra:
    - ezres elválasztó: vessző
    - tizedes jel: pont
    - excel cellába számként kerül be
    """
    if not amount_str:
        return None, ""
    amt = amount_str.replace(" ", "")
    if ',' in amt and amt.count(',') == 1:
        amt = amt.replace('.', '')
        amt = amt.replace(',', '.')
    elif amt.count('.') > 1 and ',' not in amt:
        parts = amt.split('.')
        tizedes = parts[-1]
        amt = ''.join(parts[:-1]) + '.' + tizedes
    try:
        num = float(amt)
        # Sztring formázás: 1,234,567.89
        str_formatted = f"{num:,.2f}"
        return num, str_formatted
    except Exception:
        return None, amount_str

def find_row_for_company(vevo_name, coface_names):
    vevo_name_lower = vevo_name.lower().strip()
    for idx, name in enumerate(coface_names):
        if vevo_name_lower == name.lower().strip():
            return idx
    idx = best_fuzzy_match(vevo_name, coface_names, threshold=0.80)
    if idx is not None:
        return idx
    vevo_first_word = vevo_name_lower.split()[0] if vevo_name_lower.split() else ""
    for idx, name in enumerate(coface_names):
        coface_words = name.lower().split()
        if coface_words and vevo_first_word == coface_words[0]:
            return idx
    return None

def fill_coface_excel_and_open(coface_excel_path, vevok_csv_path):
    with open(vevok_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        vevok_data = [(row.get("Vevő", "").strip(), row.get("Forintosítva HUF", "")) for row in reader]

    wb = load_workbook(coface_excel_path)
    ws = wb.active
    if ws is None:
        raise Exception("Nem sikerült megnyitni az aktív munkalapot!")

    header_row_idx, header = None, []
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=10), 1):
        header = [str(cell.value).strip() if cell.value else "" for cell in row]
        if "Cégnév" in header and "Számlázott összeg" in header:
            header_row_idx = i
            break
    if header_row_idx is None:
        raise Exception("Nem található 'Cégnév' és 'Számlázott összeg' fejléc!")

    cegnev_col = header.index("Cégnév")
    osszeg_col = header.index("Számlázott összeg")

    coface_rows = list(ws.iter_rows(min_row=header_row_idx+1, max_row=ws.max_row))
    coface_names = [
        str(row[cegnev_col].value or "").strip()
        for row in coface_rows
    ]

    from openpyxl.cell.cell import MergedCell
    for vevo_name, amount in vevok_data:
        if not vevo_name:
            continue
        idx = find_row_for_company(vevo_name, coface_names)
        if idx is not None:
            target_row = coface_rows[idx]
            cell = target_row[osszeg_col]
            if not isinstance(cell, MergedCell):
                num_value, str_formatted = format_amount(amount)
                if num_value is not None:
                    cell.value = num_value
                    cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1  # '1,234,567.89'
                else:
                    cell.value = amount

    output_path = os.path.join(os.path.dirname(coface_excel_path), "coface_output.xlsx")
    wb.save(output_path)
    try:
        if sys.platform.startswith('darwin'):
            os.system(f'open "{output_path}"')
        elif os.name == 'nt':
            os.startfile(output_path)
        else:
            os.system(f'xdg-open "{output_path}"')
    except Exception:
        pass

    return output_path