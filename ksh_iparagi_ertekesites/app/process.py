from pathlib import Path
from openpyxl import Workbook, load_workbook
import csv

class Processor:
    def process(self, ksh_path: str, matstamm_path: str, output_path: str, progress_callback=None) -> str:
        ksh = Path(ksh_path)
        mat = Path(matstamm_path)
        output = Path(output_path)
        if not ksh.exists():
            raise FileNotFoundError(f"KSH fájl nem található: {ksh}")
        if not mat.exists():
            raise FileNotFoundError(f"Matstamm fájl nem található: {mat}")

        ksh_rows = self._read_unicode_text_file(ksh)
        total_ksh = len(ksh_rows)
        total_mat = self._count_matstamm_rows(mat)
        total = total_ksh + total_mat if total_ksh + total_mat > 0 else 1
        done = 0

        ksh_sheetname = ksh.stem
        wb = Workbook()
        if wb.active is None:
            ws_ksh = wb.create_sheet(title=ksh_sheetname)
        else:
            ws_ksh = wb.active
            ws_ksh.title = ksh_sheetname

        for row in ksh_rows:
            ws_ksh.append([self._convert_cell(cell) for cell in row])
            done += 1
            if progress_callback:
                progress_callback(int(done / total * 100))

        if "matstamm_hu" in wb.sheetnames:
            wb.remove(wb["matstamm_hu"])
        ws_matstamm = wb.create_sheet("matstamm_hu")

        mat_wb = load_workbook(mat, read_only=True)
        mat_ws = mat_wb.worksheets[0]
        for row in mat_ws.iter_rows(values_only=True):
            ws_matstamm.append([self._convert_cell(cell) for cell in row])
            done += 1
            if progress_callback:
                progress_callback(int(done / total * 100))
        mat_wb.close()

        wb.save(output)
        if progress_callback:
            progress_callback(100)
        return str(output)

    def _read_unicode_text_file(self, path: Path):
        with open(path, "r", encoding="utf-16le", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            return [row for row in reader]

    def _count_matstamm_rows(self, mat_path: Path):
        mat_wb = load_workbook(mat_path, read_only=True)
        mat_ws = mat_wb.worksheets[0]
        count = mat_ws.max_row
        mat_wb.close()
        return count

    def _convert_cell(self, cell):
        if cell is None:
            return ""
        cell_str = str(cell).strip()
        if cell_str == "":
            return ""
        try:
            if "." in cell_str or "," in cell_str:
                cell_str_norm = cell_str.replace(",", ".")
                val = float(cell_str_norm)
                if val.is_integer():
                    return int(val)
                return val
            else:
                return int(cell_str)
        except Exception:
            return cell_str