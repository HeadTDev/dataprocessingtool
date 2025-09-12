from pathlib import Path
import csv
import openpyxl
from openpyxl.styles import PatternFill
from tkinter import Tk, filedialog
import shutil

class Processor:
    def process(self, ksh_path: str, matstamm_path: str) -> str:
        project_root = Path(__file__).resolve().parent.parent
        output_dir = project_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_csv_path = output_dir / "data.csv"
        output_xlsx_path = output_dir / "data.xlsx"

        # 1. KSH Unicode text beolvasása (UTF-16LE, tab-delimited)
        with open(ksh_path, "r", encoding="utf-16le", newline='') as f:
            reader = csv.reader(f, delimiter="\t")
            rows = [row for row in reader]

        # 2. Törlendő sorok: 1,2,4,5 (0-,1-,3-,4-index)
        rows_to_delete = {0, 1, 3, 4}
        cleaned_rows = [row for i, row in enumerate(rows) if i not in rows_to_delete]
        if not cleaned_rows or len(cleaned_rows) < 2:
            raise ValueError("A bemeneti fájl túl kevés sort tartalmaz a feldolgozáshoz.")

        # 3. Fejléc és adatsorok
        header = cleaned_rows[0]
        data_rows = cleaned_rows[1:]

        # 4. MATSTAMM beolvasása: "Anyag" és "Beszerzés fajtája" kigyűjtése
        mat_lookup = {}
        wb = openpyxl.load_workbook(matstamm_path, read_only=True, data_only=True)
        ws = wb.active
        mat_header = [str(cell.value).strip() if cell.value is not None else "" for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        try:
            anyag_idx = mat_header.index("Anyag")
            beszerzes_idx = mat_header.index("Beszerzés fajtája")
        except ValueError as e:
            raise ValueError("A Matstamm fájl fejlécében nem található 'Anyag' vagy 'Beszerzés fajtája' oszlop.") from e

        for row in ws.iter_rows(min_row=2):
            anyag = str(row[anyag_idx].value).strip() if row[anyag_idx].value is not None else ""
            beszerzes = str(row[beszerzes_idx].value).strip() if row[beszerzes_idx].value is not None else ""
            if anyag:
                mat_lookup[anyag] = beszerzes
        wb.close()

        try:
            data_anyag_idx = header.index("Anyag")
        except ValueError:
            raise ValueError("A KSH fájl fejlécében nincs 'Anyag' oszlop.")

        # 5. Új fejléc: "Iparági értékesítés"
        new_header = header + ["Iparági értékesítés"]
        new_data_rows = []
        for row in data_rows:
            while len(row) < len(header):
                row.append("")
            anyag_val = str(row[data_anyag_idx]).strip()
            iparagi_ertekesites = mat_lookup.get(anyag_val, "")
            new_row = row + [iparagi_ertekesites]
            new_data_rows.append(new_row)

        # Magyar számformátumot (pl. 2.126,37) float-ra váltó segédfüggvény
        def hu_to_float(cell):
            if not cell or cell.strip() == "":
                return 0.0
            s = str(cell).replace(" ", "")
            s = s.replace(".", "")    # ezres tagoló pont eltűnik
            s = s.replace(",", ".")   # tizedes vesszőből pont lesz
            try:
                return float(s)
            except Exception:
                return 0.0

        # 6. Újranyitás: Egyenleg és pénznem oszlop beszúrása a Jóváírás utáni üres fejlécű (pénznem) oszlop UTÁN
        final_header = new_header
        final_data_rows = new_data_rows

        def find_first_named_index(header_row, name):
            for idx, cell in enumerate(header_row):
                if cell.strip() == name:
                    return idx
            raise ValueError(f"{name} oszlop nem található a fejlécben.")

        jovairas_idx = find_first_named_index(final_header, "Jóváírás")
        penznem_idx = None
        for i in range(jovairas_idx + 1, len(final_header)):
            if final_header[i].strip() == "":
                penznem_idx = i
                break
        if penznem_idx is None:
            raise ValueError("Nem található üres pénznem oszlop a Jóváírás után.")
        egyenleg_value_idx = penznem_idx + 1

        egysites_header = (
            final_header[:egyenleg_value_idx]
            + ["Egyenleg", ""]
            + final_header[egyenleg_value_idx:]
        )

        egysites_data_rows = []
        for row in final_data_rows:
            while len(row) < len(final_header):
                row.append("")
            jovairas_value = row[jovairas_idx]
            jovairas_currency = row[penznem_idx]
            forgalom_idx = None
            for i in range(jovairas_idx - 1, -1, -1):
                if final_header[i].strip() == "Forgalom":
                    forgalom_idx = i
                    break
            if forgalom_idx is None:
                raise ValueError("Forgalom oszlop nem található a Jóváírás előtt!")
            forgalom_penznem_idx = None
            for i in range(forgalom_idx + 1, len(final_header)):
                if final_header[i].strip() == "":
                    forgalom_penznem_idx = i
                    break
            if forgalom_penznem_idx is None:
                raise ValueError("Forgalom pénznem oszlop nem található!")
            forgalom_value = row[forgalom_idx]
            forgalom_currency = row[forgalom_penznem_idx]

            forgalom_val = hu_to_float(forgalom_value)
            jovairas_val = hu_to_float(jovairas_value)
            egyenleg_val = forgalom_val + jovairas_val
            egyenleg_cur = forgalom_currency or jovairas_currency or ""

            new_row = (
                row[:egyenleg_value_idx]
                + [f"{egyenleg_val}", egyenleg_cur]
                + row[egyenleg_value_idx:]
            )
            egysites_data_rows.append(new_row)

        # 7. Mentsük le a data.csv-t (helyes float értékekkel a számmezőkben)
        with open(output_csv_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(egysites_header)
            writer.writerows(egysites_data_rows)

        # 8. XLSX: fejlécre szűrő + kiemelt oszlopok színezése + automatikus oszlopszélesség
        import string
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Adatok"
        with open(output_csv_path, "r", encoding="utf-8", newline='') as f:
            reader = list(csv.reader(f, delimiter=";"))

            # Fejléc
            ws.append(reader[0])

            # Adatok
            for row in reader[1:]:
                excel_row = []
                for cell in row:
                    try:
                        if cell.strip() == "":
                            excel_row.append("")
                        else:
                            # float-tá konvertáljuk, ha lehet
                            excel_row.append(float(cell))
                    except Exception:
                        excel_row.append(cell)
                ws.append(excel_row)

            max_row = ws.max_row
            max_col = ws.max_column

            # Szűrő a fejlécre
            ws.auto_filter.ref = ws.dimensions

            # Kiemelés: Forgalom, Jóváírás, Egyenleg, Iparági értékesítés
            header = reader[0]
            highlight_names = ["Forgalom", "Jóváírás", "Egyenleg", "Iparági értékesítés"]
            highlight_cols = []
            for idx, name in enumerate(header):
                if name.strip() in highlight_names:
                    highlight_cols.append(idx + 1)  # 1-based

            yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            for col in highlight_cols:
                for row in range(2, max_row + 1):  # 2-től, mert 1. sor a fejléc
                    ws.cell(row=row, column=col).fill = yellow_fill

            # Automatikus oszlopszélesség
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter  # get_column_letter(idx+1) helyett
                for cell in col:
                    try:
                        cell_value = str(cell.value) if cell.value is not None else ""
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)
                    except Exception:
                        pass
                ws.column_dimensions[column].width = max_length + 2  # egy kis ráhagyás

        wb.save(output_xlsx_path)

        # 9. Felugró mentési ablak, hogy a felhasználó kiválaszthassa a végleges helyet
        output_message = ""
        try:
            root = Tk()
            root.withdraw()
            file_path = filedialog.asksaveasfilename(
                initialfile="data.xlsx",
                title="Kimeneti XLSX fájl mentése",
                defaultextension=".xlsx",
                filetypes=[("Excel file", "*.xlsx"), ("All files", "*.*")]
            )
            if file_path:
                wb.save(file_path)
                try:
                    shutil.rmtree(output_dir)
                    output_message = f"Az XLSX fájl sikeresen elmentve ide: {file_path}\nAz output mappa törlésre került."
                except Exception as e:
                    output_message = (
                        f"Az XLSX fájl sikeresen elmentve ide: {file_path}\n"
                        f"Figyelem, az output mappa törlése sikertelen: {e}"
                    )
            else:
                output_message = (
                    f"Mentés megszakítva. Az ideiglenes XLSX fájl itt található: {output_xlsx_path}\n"
                    f"Az output mappa NEM lett törölve."
                )
        except Exception as e:
            output_message = (
                f"Hiba a mentési ablaknál: {e}\n"
                f"Az ideiglenes XLSX fájl itt található: {output_xlsx_path}\n"
                f"Az output mappa NEM lett törölve."
            )

        return output_message