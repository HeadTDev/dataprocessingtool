import re

def extract_invoice_data_from_unicode_text(filename):
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
                            result.append([
                                vevo_nev,
                                szamla_szam,
                                osszeg_bp,
                                bp_penznem,
                                osszeg_sp,
                                sp_penznem
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
                            if szamla_szam and (osszeg_bp or osszeg_sp):
                                result.append([
                                    vevo_nev,
                                    szamla_szam,
                                    osszeg_bp,
                                    bp_penznem,
                                    osszeg_sp,
                                    sp_penznem
                                ])
            break
        except Exception:
            continue
    return result