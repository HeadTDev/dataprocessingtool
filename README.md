# DataProcessingTool

A desktop suite of focused data-processing utilities for recurring back-office tasks — Excel/PDF/CSV wrangling, SAP/Coface reconciliation, and industry-report generation — presented as a single application instead of a pile of one-off scripts.

Built with **PySide6**, packaged as a standalone Windows executable, and self-updating via GitHub releases.

## Modules

| Module | Purpose |
|---|---|
| **KSH Iparági Értékesítés** | Merges a KSH sales export with a Matstamm lookup table, computes balances, and produces a formatted XLSX report. |
| **Merkantil PDF Feldolgozó** | Extracts vehicle cost line items from PDF invoices, categorizes and sums them, cross-references cost centers from Excel, and exports a CSV. |
| **Cofanet Help** | Parses a SAP text export, fuzzy-matches customer names against a Coface Excel template, and fills in the reconciled amounts. |
| **Vonalkód PDF Másolás** | Matches barcodes listed in an Excel sheet to PDF filenames in a folder and copies the matches to an output folder. |
| **Mouse Mover** | Background utility that simulates natural cursor movement to prevent an idle/away status. |

Each module runs as an independent page in a single window — pick one from the sidebar, drop in your files, and process. Mouse Mover stays available at all times as a persistent bottom-bar toggle, since it's a background state rather than a one-shot task.

## Tech stack

- **UI**: PySide6, [qtawesome](https://github.com/spyder-ide/qtawesome) (Phosphor icons)
- **Data processing**: pandas, openpyxl, xlsxwriter
- **PDF parsing**: PyPDF2
- **Logging**: [loguru](https://github.com/Delgan/loguru) — one rotating, compressed log file per module under `logs/<module>/`
- **Packaging**: PyInstaller
- **Updates**: built-in incremental self-updater, backed by GitHub releases

## Getting started

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python main.pyw
```

## Building a standalone executable

```bash
pyinstaller build/pyinstaller.spec
```

The build bundles the `icons/` folder and `version.json`, and produces a windowless `DataProcessingTool.exe`.

## Project layout

```
app/
├── backend/
│   ├── modules/<module>/   # service.py (+ parser/excel_writer where applicable) - business logic, no Qt
│   ├── services/           # logging, auto-update
│   └── workers/            # QThread-based background task runner shared by every module
├── frontend/
│   ├── modules/<module>/   # view.py - PySide6 UI for each module
│   ├── components/         # shared widgets (drag&drop inputs, CSV viewer, dialogs)
│   ├── main_window.py      # application shell: sidebar + content stack + footer
│   └── theme.py            # design tokens (color/spacing/radius) and stylesheets
└── config/                 # paths, settings, constants
```

Business logic and Qt UI are kept in separate trees by design, so the processing functions can be tested and reused without a running GUI.

## Data handling

Modules that touch business data (customer names, invoice amounts, vehicle costs) clean up their own intermediate files once the final output is produced or the result view is closed — no processed data is left behind on disk beyond what the user explicitly saves.

## License

GPL-3.0 - see [LICENSE](LICENSE).
