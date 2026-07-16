import csv
import shutil
from pathlib import Path

import pandas as pd
import xlsxwriter

from app.config.paths import module_output_dir


class Processor:
    def process(
        self,
        ksh_path: str,
        matstamm_path: str,
        save_path: str | None = None,
        progress_callback=None,
        is_cancelled=None,
    ):
        try:
            return self._process(
                ksh_path,
                matstamm_path,
                save_path=save_path,
                progress_callback=progress_callback,
                is_cancelled=is_cancelled,
            )
        except InterruptedError:
            return {"cancelled": True, "output_path": None, "row_count": 0}

    def _raise_if_cancelled(self, is_cancelled=None):
        if is_cancelled and is_cancelled():
            raise InterruptedError("A feldolgozás megszakítva.")

    def _process(
        self,
        ksh_path: str,
        matstamm_path: str,
        save_path: str | None = None,
        progress_callback=None,
        is_cancelled=None,
    ):
        output_dir = module_output_dir("ksh")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_csv_path = output_dir / "data.csv"
        output_xlsx_path = output_dir / "data.xlsx"

        if progress_callback:
            progress_callback("KSH fájl beolvasása...", 0, 0)
        with open(ksh_path, "r", encoding="utf-16le", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = [row for row in reader]

        self._raise_if_cancelled(is_cancelled)
        rows_to_delete = {0, 1, 2, 4, 5}
        cleaned_rows = [row for i, row in enumerate(rows) if i not in rows_to_delete]
        if len(cleaned_rows) < 2:
            raise ValueError(
                "A bemeneti fájl túl kevés sort tartalmaz a feldolgozáshoz."
            )

        header = cleaned_rows[0]
        data_rows = cleaned_rows[1:]

        if progress_callback:
            progress_callback("Matstamm beolvasása (Pandas + Calamine motorral)...", 0, 0)
        
        # PANDAS + CALAMINE OPTIMALIZÁCIÓ
        try:
            df_mat = pd.read_excel(
                matstamm_path,
                engine="calamine",
                usecols=lambda x: str(x).strip() in ["Anyag", "Beszerzés fajtája"],
                dtype=str,
            )
        except Exception as e:
            raise ValueError(f"Hiba a Matstamm fájl beolvasásakor: {e}")

        anyag_col = next((c for c in df_mat.columns if str(c).strip() == "Anyag"), None)
        besz_col = next((c for c in df_mat.columns if str(c).strip() == "Beszerzés fajtája"), None)

        if not anyag_col or not besz_col:
            raise ValueError(
                "A Matstamm fájl fejlécében nem található 'Anyag' vagy 'Beszerzés fajtája' oszlop."
            )

        df_mat = df_mat.dropna(subset=[anyag_col])
        mat_lookup = dict(
            zip(
                df_mat[anyag_col].astype(str).str.strip(),
                df_mat[besz_col].fillna("").astype(str).str.strip(),
            )
        )

        try:
            data_anyag_idx = header.index("Anyag")
        except ValueError:
            raise ValueError("A KSH fájl fejlécében nincs 'Anyag' oszlop.")

        new_header = header.copy()
        if new_header[-1].strip() != "":
            new_header.append("")
        new_header.append("Iparági értékesítés")

        new_data_rows = []
        total_data_rows = len(data_rows)
        for index, row in enumerate(data_rows, start=1):
            self._raise_if_cancelled(is_cancelled)
            # Ne floodoljuk a GUI-t másodpercenként 1000 eventtel, csak 10000 soronként szóljunk
            if progress_callback and index % 10000 == 0:
                progress_callback("KSH sorok kiegészítése...", index, total_data_rows)
            while len(row) < len(header):
                row.append("")
            anyag_val = str(row[data_anyag_idx]).strip()
            iparagi_ertekesites = mat_lookup.get(anyag_val, "")
            new_row = row.copy()
            if len(new_row) < len(new_header) - 1:
                new_row.append("")
            new_row.append(iparagi_ertekesites)
            new_data_rows.append(new_row)

        def to_clean_float(cell):
            if not cell or str(cell).strip() == "":
                return None
            s = str(cell).replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None

        def find_first_named_index(header_row, name):
            for idx, cell in enumerate(header_row):
                if cell.strip() == name:
                    return idx
            raise ValueError(f"{name} oszlop nem található a fejlécben.")

        jovairas_idx = find_first_named_index(new_header, "Jóváírás")
        penznem_idx = next(
            (
                i
                for i in range(jovairas_idx + 1, len(new_header))
                if new_header[i].strip() == ""
            ),
            None,
        )
        if penznem_idx is None:
            raise ValueError("Nem található üres pénznem oszlop a Jóváírás után.")
        egyenleg_value_idx = penznem_idx + 1

        egysites_header = (
            new_header[:egyenleg_value_idx]
            + ["Egyenleg", ""]
            + new_header[egyenleg_value_idx:]
        )

        forgalom_idx = next(
            (
                i
                for i in range(jovairas_idx - 1, -1, -1)
                if new_header[i].strip() == "Forgalom"
            ),
            None,
        )
        if forgalom_idx is None:
            raise ValueError("Forgalom oszlop nem található a Jóváírás előtt!")
        forgalom_penznem_idx = next(
            (
                i
                for i in range(forgalom_idx + 1, len(new_header))
                if new_header[i].strip() == ""
            ),
            None,
        )
        if forgalom_penznem_idx is None:
            raise ValueError("Forgalom pénznem oszlop nem található!")

        egysites_data_rows = []
        total_rows = len(new_data_rows)
        for index, row in enumerate(new_data_rows, start=1):
            self._raise_if_cancelled(is_cancelled)
            if progress_callback and index % 10000 == 0:
                progress_callback("Egyenleg számítása...", index, total_rows)
            while len(row) < len(new_header):
                row.append("")
            jovairas_value = row[jovairas_idx]
            jovairas_currency = row[penznem_idx]
            forgalom_value = row[forgalom_idx]
            forgalom_currency = row[forgalom_penznem_idx]
            forgalom_val = to_clean_float(forgalom_value)
            jovairas_val = to_clean_float(jovairas_value)
            egyenleg_val = (forgalom_val or 0.0) + (jovairas_val or 0.0)
            egyenleg_cur = forgalom_currency or jovairas_currency or ""
            new_row = (
                row[:egyenleg_value_idx]
                + [f"{egyenleg_val:.2f}", egyenleg_cur]
                + row[egyenleg_value_idx:-2]
                + [row[-2], row[-1]]
            )
            egysites_data_rows.append(new_row)

        if progress_callback:
            progress_callback("CSV mentése...", 0, 0)
        with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(egysites_header)
            writer.writerows(egysites_data_rows)

        final_output_path = Path(save_path) if save_path else output_xlsx_path

        if progress_callback:
            progress_callback("XLSX írása (xlsxwriter)...", 0, 0)

        # XLSXWRITER OPTIMALIZÁCIÓ
        wb = xlsxwriter.Workbook(final_output_path)
        ws = wb.add_worksheet("Adatok")

        # Stílusok
        yellow_format = wb.add_format({"bg_color": "#FFFF00"})

        highlight_names = {"Forgalom", "Jóváírás", "Egyenleg", "Iparági értékesítés"}
        highlight_cols = [
            idx
            for idx, name in enumerate(egysites_header)
            if name.strip() in highlight_names
        ]

        egyenleg_col_idx = None
        iparagi_col_idx = None
        for idx, name in enumerate(egysites_header):
            if name.strip() == "Egyenleg":
                egyenleg_col_idx = idx
            if name.strip() == "Iparági értékesítés":
                iparagi_col_idx = idx

        # Oszlopszélességek mérése indulásként a fejlécek alapján
        col_widths = [len(str(h)) for h in egysites_header]

        # Fejléc írása
        for col_num, col_name in enumerate(egysites_header):
            if col_num in highlight_cols:
                ws.write(0, col_num, col_name, yellow_format)
            else:
                ws.write(0, col_num, col_name)

        # Adatok írása
        for row_num, row_data in enumerate(egysites_data_rows, start=1):
            self._raise_if_cancelled(is_cancelled)
            if progress_callback and row_num % 10000 == 0:
                progress_callback("Excel sorok írása...", row_num, total_rows)
            for col_num, cell_data in enumerate(row_data):
                val_to_write = cell_data
                if col_num == egyenleg_col_idx:
                    try:
                        val_to_write = round(float(cell_data), 2)
                    except Exception:
                        pass
                elif col_num != iparagi_col_idx:
                    num = to_clean_float(cell_data)
                    if num is not None:
                        val_to_write = num
                
                # Max szélesség dinamikus frissítése
                str_val = str(val_to_write) if val_to_write is not None else ""
                if len(str_val) > col_widths[col_num]:
                    col_widths[col_num] = len(str_val)
                
                # Cella írása
                if col_num in highlight_cols:
                    ws.write(row_num, col_num, val_to_write, yellow_format)
                else:
                    ws.write(row_num, col_num, val_to_write)

        # Autofilter felrakása
        ws.autofilter(0, 0, len(egysites_data_rows), len(egysites_header) - 1)

        # Oszlopszélességek alkalmazása a legvégén, egy lépésben
        for col_num, width in enumerate(col_widths):
            ws.set_column(col_num, col_num, width + 2)

        wb.close()

        cleanup_message = ""
        if save_path:
            try:
                shutil.rmtree(output_dir)
                cleanup_message = "Az output mappa törlésre került."
            except Exception as exc:
                cleanup_message = f"Figyelem, az output mappa törlése sikertelen: {exc}"

        return {
            "cancelled": False,
            "output_path": str(final_output_path),
            "row_count": total_rows,
            "cleanup_message": cleanup_message,
        }
