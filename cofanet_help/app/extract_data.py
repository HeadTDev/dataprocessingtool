import re

def extract_invoice_summary(filename):
    """
    Csak a 'Név' és minden '** Számla' sort gyűjti ki.
    Minden '** Számla' sorhoz hozzárendeli a legutóbbi 'Név' értéket,
    és pontosan kiolvassa az összegeket a sor végéről.
    A 'praktiker' cégeket összevonja 'Praktiker Kft.' név alá, összegeiket összeadja.
    """
    encodings = ['utf-16', 'utf-8']
    results = []
    cegnev = None

    nev_re = re.compile(r'^\s*Név\s+(.*)$')
    szamla_re = re.compile(r'^\s*\*\*\s*Számla\s+(\d+)')
    # Kifejezetten a sor végéről szedjük az összegeket és pénznemeket!
    amounts_re = re.compile(r'([\d\.,]+)\s+(HUF|EUR)\s+([\d\.,]+)\s+(HUF|EUR)\s*$')

    for encoding in encodings:
        try:
            with open(filename, encoding=encoding) as f:
                for line in f:
                    line = line.rstrip('\n')
                    m_nev = nev_re.match(line)
                    if m_nev:
                        cegnev = m_nev.group(1).strip()
                        continue
                    m_szamla = szamla_re.match(line)
                    if m_szamla:
                        m_amounts = amounts_re.search(line.replace('\t', ' '))
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
            break
        except Exception:
            continue

    # PRAKTIKER összevonás
    praktiker_key = "Praktiker Kft."
    summarized = {}
    for row in results:
        company = row["cegnev"]
        is_praktiker = "praktiker" in company.lower()
        key = praktiker_key if is_praktiker else company

        # Segéd: magyar számformátum str -> float
        def to_float(val):
            if not val:
                return 0.0
            val = val.replace('.', '').replace(',', '.')
            try:
                return float(val)
            except Exception:
                return 0.0

        if key not in summarized:
            summarized[key] = {
                "cegnev": key,
                "osszeg_bp": 0.0,
                "bp_penznem": row["bp_penznem"],
                "osszeg_sp": 0.0,
                "sp_penznem": row["sp_penznem"]
            }
        summarized[key]["osszeg_bp"] += to_float(row["osszeg_bp"])
        summarized[key]["osszeg_sp"] += to_float(row["osszeg_sp"])
        # Pénznemek: ha üres, akkor vegyük a következőt, különben az elsőt
        if not summarized[key]["bp_penznem"]:
            summarized[key]["bp_penznem"] = row["bp_penznem"]
        if not summarized[key]["sp_penznem"]:
            summarized[key]["sp_penznem"] = row["sp_penznem"]

    # Visszaalakítjuk magyar formátumra
    def format_hu(val):
        return f'{val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    output_rows = []
    for data in summarized.values():
        output_rows.append({
            "cegnev": data["cegnev"],
            "osszeg_bp": format_hu(data["osszeg_bp"]),
            "bp_penznem": data["bp_penznem"],
            "osszeg_sp": format_hu(data["osszeg_sp"]),
            "sp_penznem": data["sp_penznem"]
        })

    # Betűrendbe rendezés cégnév szerint
    output_rows.sort(key=lambda x: x["cegnev"].lower())
    return output_rows

def write_vevok_csv(results, output_path):
    import csv
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "cegnev", "osszeg_bp", "bp_penznem", "osszeg_sp", "sp_penznem"
        ])
        writer.writeheader()
        for row in results:
            writer.writerow(row)