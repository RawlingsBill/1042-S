"""
Pure-Python validation functions for 1042-S form data.

Each function receives the data as a list of row-dicts (as produced by
pandas.DataFrame.to_dict(orient="records")) plus any required reference-data
lists loaded from the JSON files, and returns a list of error rows ready to
be written to a CSV.
"""

import math


def validate_tax_rates(data_dict, tax_data):
    """BOX3B / BOX4B: both must be IRS-approved treaty rates."""
    rows = []
    for x in data_dict:
        match3b = any(float(x["BOX3B_TAX RATE"]) == float(i) for i in tax_data)
        match4b = any(float(x["BOX4B_TAX RATE"]) == float(i) for i in tax_data)
        if not match3b or not match4b:
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                x["BOX3B_TAX RATE"],
                x["BOX4B_TAX RATE"],
                "Not a valid tax rate.",
            ])
    return rows


def validate_box7a(data_dict):
    """BOX7A: withheld amount must match tax_rate × gross_income / 100."""
    rows = []
    for x in data_dict:
        rate3b = float(x["BOX3B_TAX RATE"])
        rate4b = float(x["BOX4B_TAX RATE"])
        withheld = x["BOX7A_FEDERAL TAX WITHHELD"]

        if rate3b == 0 and rate4b == 0 and withheld != 0:
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                str(withheld),
                "Tax rate is 0, but tax withheld.",
            ])
        if math.isnan(rate3b):
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                str(withheld),
                "Not valid tax rate.",
            ])
        if rate3b != 0 and not math.isnan(rate3b):
            tax_owed = round((rate3b * float(x["BOX2_GROSS INCOME"])) / 100)
            if tax_owed != float(withheld):
                rows.append([
                    x["BOX13A_RECIPIENT NAME1"],
                    str(withheld),
                    "Tax withheld is not correct amount(Tax rate x Gross Income).",
                ])
        if math.isnan(rate4b):
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                str(withheld),
                "Not valid tax rate.",
            ])
        if rate4b != 0 and not math.isnan(rate4b):
            tax_owed = round(rate4b * float(x["BOX2_GROSS INCOME"]) / 100)
            if tax_owed != float(withheld):
                rows.append([
                    x["BOX13A_RECIPIENT NAME1"],
                    str(withheld),
                    "Tax withheld is not correct amount(Tax rate x Gross Income).",
                ])
    return rows


def validate_box10(data_dict):
    """BOX10: must equal BOX7A + BOX8 + BOX9 (NaN treated as 0)."""
    rows = []
    for x in data_dict:
        box7a = float(x["BOX7A_FEDERAL TAX WITHHELD"])
        if math.isnan(box7a):
            box7a = 0
        box8 = float(x["BOX8_TAX WITHHELD OTHER AGENTS"])
        if math.isnan(box8):
            box8 = 0
        box9 = float(x["BOX9_TAX PAID WITHHOLDING AGENT"])
        if math.isnan(box9):
            box9 = 0

        if box7a + box8 + box9 != float(x["BOX10_TOTAL WITHHOLDING CREDIT"]):
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                str(x["BOX10_TOTAL WITHHOLDING CREDIT"]),
                "Box10 not correct amount.",
            ])
    return rows


def validate_box13b(data_dict, country_data):
    """BOX13B: country code must match country name (case-insensitive)."""
    rows = []
    for x in data_dict:
        code = x["BOX13B_RECIPIENT COUNTRY CODE"].rstrip()
        name = str(x["BOX13D_RECIPIENT COUNTRY"]).rstrip()
        if name == "nan":
            name = "Null"
        if not isinstance(name, str):
            continue
        for i in country_data:
            if code.casefold() == i["Code"].casefold():
                if not name.casefold() == i["Name"].casefold():
                    rows.append([
                        x["BOX13A_RECIPIENT NAME1"],
                        str(code),
                        str(name),
                        "Country name does not match country code.",
                    ])
    return rows


def validate_box13d(data_dict, state_data, prov_data):
    """BOX13D: state/province codes must match country (US → state, CA → province)."""
    rows = []

    # --- State check (USA) ---
    for x in data_dict:
        match = True
        country = str(x["BOX13D_RECIPIENT COUNTRY"]).rstrip()
        if not isinstance(country, str):
            country = "null"
            state = x.get("BOX13D_RECIPIENT STATE(2LetterCode)", "null")
            if not isinstance(state, str):
                state = "null"
            rows.append([
                x["BOX13A_RECIPIENT NAME1"], str(state), "",
                str(country), "No country code and no state code provided.",
            ])
            continue

        if (country.casefold() == "united states"
                and isinstance(x["BOX13D_RECIPIENT STATE(2LetterCode)"], str)):
            match = False
            for i in state_data:
                if x["BOX13D_RECIPIENT STATE(2LetterCode)"].casefold() == i["Code"].casefold():
                    match = True
        elif country.casefold() == "united states":
            if not isinstance(x["BOX13D_RECIPIENT STATE(2LetterCode)"], str):
                x["BOX13D_RECIPIENT STATE(2LetterCode)"] = "null"
                match = False

        if not match:
            rows.append([
                x["BOX13A_RECIPIENT NAME1"],
                str(x["BOX13D_RECIPIENT STATE(2LetterCode)"]), "",
                str(country), "Country is USA but state code does not match",
            ])

    # --- Province check (Canada) ---
    for x in data_dict:
        prov = str(x["BOX13D_RECIPIENT PROVINCE(2LetterCode)"]).replace("    ", "")
        if prov == "nan":
            prov = "Null"
        country = str(x["BOX13D_RECIPIENT COUNTRY"]).rstrip()
        match = True

        if country.casefold() != "canada" and prov not in ("", "Null"):
            rows.append([
                x["BOX13A_RECIPIENT NAME1"], "", str(prov),
                str(country), "Country is not Canada but province fild not empty",
            ])
            continue

        if country.casefold() == "canada":
            match = False
            for i in prov_data:
                if prov.casefold() == i["Code"].casefold():
                    match = True
            if not match:
                rows.append([
                    x["BOX13A_RECIPIENT NAME1"], "", str(prov),
                    str(country), "Country is Canada but province code does not match",
                ])

    return rows
