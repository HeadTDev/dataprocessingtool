import re

def normalize_amount(amount_str):
    return amount_str.replace('.', '').replace(',', '.').replace(' ', '')

def format_hu_number(amount):
    try:
        amt = float(amount)
        return f"{amt:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(amount)

def convert_to_huf(amount_str, currency, eur_rate):
    try:
        amount = float(normalize_amount(amount_str))
    except Exception:
        return ""
    if currency == "EUR":
        rate = eur_rate
    elif currency == "HUF":
        rate = 1
    else:
        return ""
    return round(amount * rate, 2)

def extract_invoice_data_from_unicode_text(filename, eur_rate=400.0):
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
                            osszeg_bp, bp_penznem, osszeg_sp, sp_penznem = adatok_match.groups()
                        else:
                            # fallback: split by tab or semicolon
                            parts = re.split(r'\t|;', line)
                            szamla_match = szamla_re.search(parts[0]) if parts else None
                            szamla_szam = szamla_match.group(1) if szamla_match else ''
                            osszeg_bp = bp_penznem = osszeg_sp = sp_penznem = ''
                            for i, val in enumerate(parts):
                                next_val = parts[i+1] if i+1 < len(parts) else ''
                                if re.match(r'^[\d\s\.,"]+$', val) and next_val in ('HUF', 'EUR'):
                                    if not osszeg_bp:
                                        osszeg_bp, bp_penznem = val.replace('"','').strip(), next_val
                                    elif not osszeg_sp:
                                        osszeg_sp, sp_penznem = val.replace('"','').strip(), next_val
                        atvaltva_huf = (
                            convert_to_huf(osszeg_bp, bp_penznem, eur_rate)
                            if bp_penznem and bp_penznem != "HUF" else normalize_amount(osszeg_bp)
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