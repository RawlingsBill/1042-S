# 1042-S Form Validator

A desktop application for validating IRS Form 1042-S data before submission. Reads a CSV export of form data and produces error reports for each category of validation failure.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Input File Format](#input-file-format)
- [Validation Rules](#validation-rules)
- [Output Files](#output-files)
- [Reference Data Files](#reference-data-files)
- [Project Structure](#project-structure)
- [Building the Executable](#building-the-executable)

---

## Overview

The 1042-S Form Validator checks CSV data exports for common errors in U.S. withholding tax reporting for foreign recipients. The GUI lets you select an input file, then automatically generates up to five error-report CSVs alongside an application log — one report per validation category.

Validation categories:

| Category | Field(s) Checked |
|---|---|
| Tax Rate | BOX3B, BOX4B |
| Federal Tax Withholding | BOX7A |
| Total Withholding Credit | BOX10 |
| Country Code / Name Match | BOX13B |
| State / Province Code | BOX13D |

---

## Prerequisites

- Python 3.9+
- pip

---

## Installation

```bash
# Clone or copy the project folder, then:
cd 1042-S

# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install pandas numpy FreeSimpleGUI
```

---

## Running the Application

```bash
python main.py
```

1. A GUI window opens.
2. Click **Browse** and select your input CSV file.
3. Click **Ok**.
4. A completion popup appears when processing is finished.
5. Error-report CSVs are written to the same directory as the input file.

---

## Input File Format

The input must be a **CSV file encoded in latin-1** with columns that match IRS Form 1042-S box numbers. Required columns:

| Column Name | IRS Box | Description |
|---|---|---|
| `BOX13A_RECIPIENT NAME1` | 13a | Recipient name |
| `BOX3B_TAX RATE` | 3b | Chapter 3 withholding tax rate (%) |
| `BOX4B_TAX RATE` | 4b | Chapter 4 withholding tax rate (%) |
| `BOX2_GROSS INCOME` | 2 | Gross income subject to withholding |
| `BOX7A_FEDERAL TAX WITHHELD` | 7a | Federal tax withheld amount |
| `BOX8_WITHHOLDING BY OTHER AGENTS` | 8 | Withholding by other agents |
| `BOX9_TAX PAID WITHHOLDING AGENT` | 9 | Tax paid by withholding agent |
| `BOX10_TOTAL WITHHOLDING CREDIT` | 10 | Total withholding credit |
| `BOX13B_RECIPIENT COUNTRY CODE` | 13b | 2-letter recipient country code |
| `BOX13B_RECIPIENT COUNTRY NAME` | 13b | Recipient country name |
| `BOX13B_RECIPIENT COUNTRY` | 13b | Country identifier (used for US/CA logic) |
| `BOX13D_STATE` | 13d | State or province code |

---

## Validation Rules

### Tax Rate (BOX3B & BOX4B)

Flags any row where BOX3B or BOX4B does not appear in the list of IRS-approved treaty rates defined in `tax_rates.json`.

Valid rates: `0.0, 2.0, 4.0, 4.95, 5.0, 7.0, 8.0, 10.0, 12.0, 12.5, 14.0, 15.0, 17.5, 20.0, 25.0, 27.5, 28.0, 30.0, 35.0, 39.6`

---

### Federal Tax Withheld (BOX7A)

Flags rows under any of these conditions:

1. **Rate is 0 but withholding is non-zero** — Tax rate is 0% yet a withholding amount is present.
2. **Invalid tax rate** — Tax rate is blank/NaN.
3. **Calculation mismatch** — `BOX7A ≠ (BOX3B_TAX RATE × BOX2_GROSS INCOME) / 100`

---

### Total Withholding Credit (BOX10)

Flags rows where:

```
BOX10 ≠ BOX7A + BOX8 + BOX9
```

NaN values in BOX8 and BOX9 are treated as 0.

---

### Country Code / Name (BOX13B)

Flags rows where the 2-letter country code in BOX13B does not correspond to the country name in BOX13B, using `country_codes.json` as the reference. Comparison is case-insensitive; leading/trailing whitespace is stripped.

---

### State / Province (BOX13D)

| Recipient Country | Rule |
|---|---|
| USA | BOX13D must be a valid US state code from `state_codes.json` |
| Canada (CA) | BOX13D must be a valid Canadian province code from `can_provinces.json` |
| Other | BOX13D must be blank — a code here is flagged as an error |

---

## Output Files

All output files are written to the **same directory as the input file**. The base name of the input file is used as a prefix.

| File | Contents |
|---|---|
| `<input>_tax_rate_errors.csv` | Invalid tax rates (BOX3B / BOX4B) |
| `<input>_BOX7A_errors.csv` | Federal withholding amount errors |
| `<input>_BOX10_errors.csv` | Total withholding credit mismatches |
| `<input>_BOX13B_errors.csv` | Country code / name mismatches |
| `<input>_BOX13D_errors.csv` | State / province code errors |
| `1042-S-<YYYY-MM-DD>.log` | Application log (written to project directory) |

Each CSV includes the recipient name, the relevant field values, and a **REASON** column describing the specific error.

---

## Reference Data Files

These JSON files live in the project root and are loaded at runtime:

| File | Contents |
|---|---|
| `tax_rates.json` | Array of valid IRS treaty tax rates |
| `country_codes.json` | Array of `{"Name": "...", "Code": "..."}` objects for ~250 countries |
| `state_codes.json` | Array of `{"Name": "...", "Code": "..."}` objects for US states and territories |
| `can_provinces.json` | Array of `{"Name": "...", "Code": "..."}` objects for Canadian provinces/territories |

To add or update a valid tax rate, country, state, or province, edit the appropriate JSON file directly.

---

## Project Structure

```
1042-S/
├── main.py               # Application entry point (GUI + all validation logic)
├── test.py               # Legacy development script (not used in production)
├── tax_rates.json        # Valid IRS treaty rates
├── country_codes.json    # Country code reference data
├── state_codes.json      # US state code reference data
├── can_provinces.json    # Canadian province code reference data
├── spsgz.png             # Application logo
├── spsgz.ico             # Application icon
└── output/
    ├── 1042-S-Errors1.0.exe   # Compiled executable (v1.0)
    └── 1042-S-Errors1.1.exe   # Compiled executable (v1.1)
```

---

## Building the Executable

The application uses [PyInstaller](https://pyinstaller.org/) to produce a standalone `.exe`.

```bash
pip install pyinstaller auto-py-to-exe

# Simple one-file build
pyinstaller --onefile --windowed --icon=spsgz.ico main.py
```

Or launch the GUI builder:

```bash
auto-py-to-exe
```

The compiled executable will appear in the `dist/` folder. Copy the four JSON reference files and the `spsgz.png`/`spsgz.ico` assets into the same directory as the `.exe` before distributing.

---

*Built by Stock Plan Solutions — internal use only.*
