import re

def normalize_amount(amount_str):
    amount_str = amount_str.replace('.', '')
    amount_str = amount_str.replace(',', '.')
    amount_str = amount_str.replace(' ', '')
    return amount_str

def format_hu_number(amount):
    """
    Formázza az összeget magyar pénzügyi formátum szerint (ezres: pont, tizedes: vessző).
    Pl. 12345.67 -> '12.345,67'
    Ha nem szám, visszaadja, ami jött.
    """
    try:
        amt = float(amount)
        return f"{amt:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(amount)

def convert_to_huf(amount_str, currency, eur_rate):
    amount_str = normalize_amount(amount_str)
    try:
        amount = float(amount_str)
    except Exception:
        return ""
    if currency == "EUR":
        rate = eur_rate
    elif currency == "HUF":
        rate = 1
    else:
        return ""
    return round(amount * rate, 2)

def extract_invoice_data_from_unicode_text(filename, eur_rate: float = 400.00):
    result = []
    vevo_nev = None
    encodings = ['utf-16', 'utf-8']
    szamla_re = re.compile(r"Számla\s*(\d+)")
    adatok_re = re.compile(r'"([^"]+)"\s*(\w{3})\s*"([^"]+)"\s*(\w{3})')
    for encoding in encodings:
        try:
            with open(filename, encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("Név"):
                        vevo_nev = line.replace("Név", "").strip()
                    if line.lstrip("*").strip().startswith("Számla"):
                        szamla_match = szamla_re.search(line)
                        adatok_match = adatok_re.search(line)
                        if szamla_match and adatok_match:
                            szamla_szam = szamla_match.group(1)
                            osszeg_bp = adatok_match.group(1).strip()
                            bp_penznem = adatok_match.group(2).strip()
                            osszeg_sp = adatok_match.group(3).strip()
                            sp_penznem = adatok_match.group(4).strip()
                            atvaltva_huf = (
                                convert_to_huf(osszeg_bp, bp_penznem, eur_rate)
                                if bp_penznem != "HUF" else normalize_amount(osszeg_bp)
                            )
                            result.append([
                                vevo_nev,
                                szamla_szam,
                                format_hu_number(normalize_amount(osszeg_bp)),
                                bp_penznem,
                                format_hu_number(normalize_amount(osszeg_sp)),
                                sp_penznem,
                                format_hu_number(atvaltva_huf)
                            ])
                        else:
                            parts = re.split(r'\t|;', line)
                            szamla_match = szamla_re.search(parts[0]) if parts else None
                            szamla_szam = szamla_match.group(1) if szamla_match else ''
                            osszeg_bp = ''
                            bp_penznem = ''
                            osszeg_sp = ''
                            sp_penznem = ''
                            for i, val in enumerate(parts):
                                if re.match(r'^[\d\s\.,"]+$', val):
                                    next_val = parts[i+1] if i+1 < len(parts) else ''
                                    if next_val in ('HUF', 'EUR'):
                                        if not osszeg_bp:
                                            osszeg_bp = val.replace('"', '').strip()
                                            bp_penznem = next_val
                                        elif not osszeg_sp:
                                            osszeg_sp = val.replace('"', '').strip()
                                            sp_penznem = next_val
                            atvaltva_huf = (
                                convert_to_huf(osszeg_bp, bp_penznem, eur_rate)
                                if bp_penznem != "HUF" else normalize_amount(osszeg_bp)
                            )
                            if szamla_szam and (osszeg_bp or osszeg_sp):
                                result.append([
                                    vevo_nev,
                                    szamla_szam,
                                    format_hu_number(normalize_amount(osszeg_bp)),
                                    bp_penznem,
                                    format_hu_number(normalize_amount(osszeg_sp)),
                                    sp_penznem,
                                    format_hu_number(atvaltva_huf)
                                ])
            break
        except Exception:
            continue
    return result