"""KSH and Matstamm file processor."""

from pathlib import Path
import csv
import logging
from typing import List, Dict, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill
from PySide6.QtWidgets import QFileDialog
import shutil

from common import to_clean_float, ensure_output_dir

logger = logging.getLogger("ksh_processor")

class Processor:
    """Process KSH and Matstamm files to generate enriched Excel output."""
    
    # Configuration constants
    ROWS_TO_DELETE = {0, 1, 2, 4, 5}
    HIGHLIGHT_COLUMNS = ["Forgalom", "Jóváírás", "Egyenleg", "Iparági értékesítés"]
    
    def _read_ksh_file(self, ksh_path: str) -> tuple[List[str], List[List[str]]]:
        """Read and clean KSH CSV file."""
        logger.info(f"Reading KSH file: {ksh_path}")
        
        with open(ksh_path, "r", encoding="utf-16le", newline='') as f:
            reader = csv.reader(f, delimiter="\t")
            rows = [row for row in reader]
        
        cleaned_rows = [row for i, row in enumerate(rows) if i not in self.ROWS_TO_DELETE]
        if len(cleaned_rows) < 2:
            raise ValueError("A bemeneti fájl túl kevés sort tartalmaz a feldolgozáshoz.")
        
        logger.info(f"Cleaned {len(cleaned_rows)} rows")
        return cleaned_rows[0], cleaned_rows[1:]
    
    def _build_material_lookup(self, matstamm_path: str) -> Dict[str, str]:
        """Build material lookup using pandas for efficiency."""
        logger.info(f"Building material lookup from: {matstamm_path}")
        
        try:
            # Use pandas - more efficient than openpyxl for reading specific columns
            df = pd.read_excel(
                matstamm_path,
                usecols=["Anyag", "Beszerzés fajtája"],
                dtype=str
            )
            
            mat_lookup = {}
            for _, row in df.iterrows():
                anyag = str(row["Anyag"]).strip() if pd.notna(row["Anyag"]) else ""
                beszerzes = str(row["Beszerzés fajtája"]).strip() if pd.notna(row["Beszerzés fajtája"]) else ""
                if anyag:
                    mat_lookup[anyag] = beszerzes
            
            logger.info(f"Built lookup with {len(mat_lookup)} entries")
            return mat_lookup
            
        except KeyError:
            raise ValueError("A Matstamm fájl fejlécében nem található 'Anyag' vagy 'Beszerzés fajtája' oszlop.")
        except Exception as e:
            raise ValueError(f"Hiba a Matstamm fájl olvasásakor: {e}")
    
    @staticmethod
    def _find_column_index(header: List[str], name: str) -> int:
        """Find column index by name."""
        for idx, cell in enumerate(header):
            if cell.strip() == name:
                return idx
        raise ValueError(f"{name} oszlop nem található a fejlécben.")
    
    def process(self, ksh_path: str, matstamm_path: str) -> str:
        """
        Process KSH and Matstamm files.
        
        Args:
            ksh_path: Path to KSH CSV file
            matstamm_path: Path to Matstamm Excel file
            
        Returns:
            Output message string
        """
        logger.info(f"Starting processing: KSH={ksh_path}, Matstamm={matstamm_path}")
        
        project_root = Path(__file__).resolve().parent.parent
        output_dir = ensure_output_dir(project_root)
        output_csv_path = output_dir / "data.csv"
        output_xlsx_path = output_dir / "data.xlsx"
        
        # Step 1: Read and clean KSH file
        header, data_rows = self._read_ksh_file(ksh_path)
        
        # Step 2: Build material lookup
        mat_lookup = self._build_material_lookup(matstamm_path)
        
        # Step 3: Add Iparági értékesítés column
        try:
            data_anyag_idx = header.index("Anyag")
        except ValueError:
            raise ValueError("A KSH fájl fejlécében nincs 'Anyag' oszlop.")

        new_header = header.copy()
        if new_header[-1].strip() != "":
            new_header.append("")
        new_header.append("Iparági értékesítés")

        new_data_rows = []
        for row in data_rows:
            while len(row) < len(header):
                row.append("")
            anyag_val = str(row[data_anyag_idx]).strip()
            iparagi_ertekesites = mat_lookup.get(anyag_val, "")
            new_row = row.copy()
            if len(new_row) < len(new_header) - 1:
                new_row.append("")
            new_row.append(iparagi_ertekesites)
            new_data_rows.append(new_row)

        final_header = new_header
        final_data_rows = new_data_rows
        
        # Step 4: Add Egyenleg (balance) column
        jovairas_idx = self._find_column_index(final_header, "Jóváírás")
        penznem_idx = next((i for i in range(jovairas_idx + 1, len(final_header)) if final_header[i].strip() == ""), None)
        if penznem_idx is None:
            raise ValueError("Nem található üres pénznem oszlop a Jóváírás után.")
        egyenleg_value_idx = penznem_idx + 1
        
        # Find Forgalom column once (not in loop!)
        forgalom_idx = next((i for i in range(jovairas_idx - 1, -1, -1) if final_header[i].strip() == "Forgalom"), None)
        if forgalom_idx is None:
            raise ValueError("Forgalom oszlop nem található a Jóváírás előtt!")
        
        forgalom_penznem_idx = next((i for i in range(forgalom_idx + 1, len(final_header)) if final_header[i].strip() == ""), None)
        if forgalom_penznem_idx is None:
            raise ValueError("Forgalom pénznem oszlop nem található!")

        egysites_header = (
            final_header[:egyenleg_value_idx]
            + ["Egyenleg", ""]
            + final_header[egyenleg_value_idx:]
        )

        egysites_data_rows = []
        for row in final_data_rows:
            while len(row) < len(final_header):
                row.append("")
            
            # Calculate balance
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
        
        logger.info("Writing CSV output")
        with open(output_csv_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(egysites_header)
            writer.writerows(egysites_data_rows)
        
        logger.info("Creating Excel workbook")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Adatok"

        # Find columns to highlight (once, not repeatedly)
        egyenleg_col_idx = None
        iparagi_col_idx = None
        for idx, name in enumerate(egysites_header):
            if name.strip() == "Egyenleg":
                egyenleg_col_idx = idx
            if name.strip() == "Iparági értékesítés":
                iparagi_col_idx = idx

        with open(output_csv_path, "r", encoding="utf-8", newline='') as f:
            reader = list(csv.reader(f, delimiter=";"))
            ws.append(reader[0])
            for row in reader[1:]:
                excel_row = []
                for idx, cell in enumerate(row):
                    if idx == egyenleg_col_idx:
                        try:
                            excel_row.append(round(float(cell), 2))
                        except:
                            excel_row.append(cell)
                    elif idx == iparagi_col_idx:
                        excel_row.append(cell)
                    else:
                        num = to_clean_float(cell)
                        if num is not None:
                            excel_row.append(num)
                        else:
                            excel_row.append(cell)
                ws.append(excel_row)

            max_row = ws.max_row
            ws.auto_filter.ref = ws.dimensions

            # Highlight specific columns
            header = reader[0]
            highlight_cols = [idx + 1 for idx, name in enumerate(header) if name.strip() in self.HIGHLIGHT_COLUMNS]

            yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            for col in highlight_cols:
                for row in range(2, max_row + 1):
                    ws.cell(row=row, column=col).fill = yellow_fill

            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        cell_value = str(cell.value) if cell.value is not None else ""
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)
                    except Exception:
                        pass
                ws.column_dimensions[column].width = max_length + 2

        wb.save(output_xlsx_path)
        logger.info("Excel saved successfully")

        # Ask user for save location using PySide6
        output_message = ""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Kimeneti XLSX fájl mentése",
                "data.xlsx",
                "Excel file (*.xlsx);;All files (*.*)"
            )
            if file_path:
                wb.save(file_path)
                logger.info(f"Saved to {file_path}")
                try:
                    shutil.rmtree(output_dir)
                    output_message = f"Az XLSX fájl sikeresen elmentve ide: {file_path}\nAz output mappa törlésre került."
                except Exception as e:
                    logger.warning(f"Failed to remove output directory: {e}")
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
            logger.exception("Error during save dialog")
            output_message = (
                f"Hiba a mentési ablaknál: {e}\n"
                f"Az ideiglenes XLSX fájl itt található: {output_xlsx_path}\n"
                f"Az output mappa NEM lett törölve."
            )

        logger.info("Processing completed")
        return output_message