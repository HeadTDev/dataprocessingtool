import csv
import os

from .coface_copy import fill_coface_excel_and_open
from .extract_data import extract_invoice_summary

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def _raise_if_cancelled(is_cancelled=None):
    if is_cancelled and is_cancelled():
        raise InterruptedError("A feldolgozás megszakítva.")


def _format_hu_amount(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def process_cofanet_files(
    sap_path,
    coface_excel_path,
    eur_rate,
    save_path,
    progress_callback=None,
    is_cancelled=None,
):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        if progress_callback:
            progress_callback("SAP adatok olvasása...", 0, 0)
        summary_rows = extract_invoice_summary(
            sap_path,
            progress_callback=progress_callback,
            is_cancelled=is_cancelled,
        )
        _raise_if_cancelled(is_cancelled)

        summary_rows_sorted = sorted(summary_rows, key=lambda x: x["cegnev"].lower())
        output_path = os.path.join(OUTPUT_DIR, "vevok.csv")
        headers = [
            "Vevő",
            "Összeg BP-ben",
            "BP pénznem",
            "Összeg SP-ben",
            "SP pénznem",
            "Forintosítva HUF",
        ]

        total_rows = len(summary_rows_sorted)
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for index, row in enumerate(summary_rows_sorted, start=1):
                _raise_if_cancelled(is_cancelled)
                if progress_callback:
                    progress_callback("Vevők CSV mentése...", index, total_rows)

                osszeg_bp = row.get("osszeg_bp", "").replace(".", "").replace(",", ".")
                bp_penznem = row.get("bp_penznem", "").upper()
                try:
                    osszeg_bp_float = float(osszeg_bp) if osszeg_bp else 0.0
                except Exception:
                    osszeg_bp_float = 0.0

                if bp_penznem != "HUF":
                    forintositva_str = _format_hu_amount(osszeg_bp_float * eur_rate)
                else:
                    forintositva_str = row.get("osszeg_bp", "")

                writer.writerow(
                    [
                        row.get("cegnev", ""),
                        row.get("osszeg_bp", ""),
                        row.get("bp_penznem", ""),
                        row.get("osszeg_sp", ""),
                        row.get("sp_penznem", ""),
                        forintositva_str,
                    ]
                )

        _raise_if_cancelled(is_cancelled)
        coface_output_path = fill_coface_excel_and_open(
            coface_excel_path,
            output_path,
            save_path=save_path,
            progress_callback=progress_callback,
            is_cancelled=is_cancelled,
            open_file=False,
        )

        return {
            "cancelled": False,
            "rows_count": total_rows,
            "vevok_csv_path": output_path,
            "coface_output_path": coface_output_path,
        }
    except InterruptedError:
        return {
            "cancelled": True,
            "rows_count": 0,
            "vevok_csv_path": None,
            "coface_output_path": None,
        }
