"""
Unit tests for the 1042-S form validation logic in validators.py.

Tests work with plain Python dicts — no pandas, no GUI, no file I/O —
so they run in any Python environment that has the project JSON files.

Run from the project root:
    pytest test_main.py -v
"""

import json
import math
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from validators import (  # noqa: E402
    validate_tax_rates,
    validate_box7a,
    validate_box10,
    validate_box13b,
    validate_box13d,
)


# ---------------------------------------------------------------------------
# Load reference data once for the whole session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tax_data():
    with open(os.path.join(PROJECT_ROOT, "tax_rates.json")) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def country_data():
    with open(os.path.join(PROJECT_ROOT, "country_codes.json")) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def state_data():
    with open(os.path.join(PROJECT_ROOT, "state_codes.json")) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def prov_data():
    with open(os.path.join(PROJECT_ROOT, "can_provinces.json")) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

# A "clean" row that should produce zero errors across all validators.
# - 15% of 1000 = 150  →  BOX7A correct
# - 150 + 0 + 0 = 150  →  BOX10 correct
# - "CA" code matches "Canada"  →  BOX13B correct
# - Canada + province "ON"  →  BOX13D correct
_CLEAN = {
    "BOX13A_RECIPIENT NAME1": "Test Recipient",
    "BOX3B_TAX RATE": 15.0,
    "BOX4B_TAX RATE": 15.0,
    "BOX2_GROSS INCOME": 1000.0,
    "BOX7A_FEDERAL TAX WITHHELD": 150.0,
    "BOX8_TAX WITHHELD OTHER AGENTS": 0.0,
    "BOX9_AMOUNT REPAID RECIPIENT": 0.0,
    "BOX10_TOTAL WITHHOLDING CREDIT": 150.0,
    "BOX13B_RECIPIENT COUNTRY CODE": "CA",
    "BOX13D_RECIPIENT FOREIGN COUNTRY": "Canada",
    "BOX13D_RECIPIENT STATE(2LetterCode)": "",
    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": "ON",
}


def row(**overrides):
    """Return a clean row dict with any fields replaced by keyword args."""
    r = dict(_CLEAN)
    r.update(overrides)
    return r


def reasons(error_rows):
    return [r[-1] for r in error_rows]   # REASON is always the last column


# ---------------------------------------------------------------------------
# Tax Rate  (BOX3B / BOX4B)
# ---------------------------------------------------------------------------

class TestTaxRate:

    def test_valid_rate_no_error(self, tax_data):
        assert validate_tax_rates([row()], tax_data) == []

    def test_invalid_box3b_flagged(self, tax_data):
        errors = validate_tax_rates([row(**{"BOX3B_TAX RATE": 99.0})], tax_data)
        assert len(errors) == 1
        assert "not a valid tax rate" in errors[0][-1].lower()

    def test_invalid_box4b_flagged(self, tax_data):
        errors = validate_tax_rates([row(**{"BOX4B_TAX RATE": 99.0})], tax_data)
        assert len(errors) == 1

    def test_zero_rate_is_valid(self, tax_data):
        errors = validate_tax_rates(
            [row(**{"BOX3B_TAX RATE": 0.0, "BOX4B_TAX RATE": 0.0,
                    "BOX7A_FEDERAL TAX WITHHELD": 0.0,
                    "BOX10_TOTAL WITHHOLDING CREDIT": 0.0})],
            tax_data,
        )
        assert errors == []

    def test_every_approved_rate_accepted(self, tax_data):
        """Every rate in tax_rates.json must pass validation."""
        for rate in tax_data:
            withheld = round(float(rate) * 1000 / 100)
            errors = validate_tax_rates(
                [row(**{"BOX3B_TAX RATE": float(rate), "BOX4B_TAX RATE": float(rate),
                        "BOX7A_FEDERAL TAX WITHHELD": withheld,
                        "BOX10_TOTAL WITHHOLDING CREDIT": withheld})],
                tax_data,
            )
            assert errors == [], f"Approved rate {rate} was incorrectly flagged"

    def test_only_bad_row_flagged_in_mixed_batch(self, tax_data):
        rows = [
            row(**{"BOX13A_RECIPIENT NAME1": "Good"}),
            row(**{"BOX13A_RECIPIENT NAME1": "Bad", "BOX3B_TAX RATE": 99.0}),
        ]
        errors = validate_tax_rates(rows, tax_data)
        names = [e[0] for e in errors]
        assert "Bad" in names
        assert "Good" not in names


# ---------------------------------------------------------------------------
# BOX7A  Federal Tax Withheld
# ---------------------------------------------------------------------------

class TestBOX7A:

    def test_correct_withholding_no_error(self):
        # 15% × 1000 = 150
        assert validate_box7a([row()]) == []

    def test_zero_rate_zero_withheld_no_error(self):
        assert validate_box7a([row(**{
            "BOX3B_TAX RATE": 0.0, "BOX4B_TAX RATE": 0.0,
            "BOX7A_FEDERAL TAX WITHHELD": 0.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 0.0,
        })]) == []

    def test_zero_rate_nonzero_withheld_flagged(self):
        errors = validate_box7a([row(**{
            "BOX3B_TAX RATE": 0.0, "BOX4B_TAX RATE": 0.0,
            "BOX7A_FEDERAL TAX WITHHELD": 50.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 50.0,
        })])
        assert any("tax rate is 0" in r.lower() for r in reasons(errors))

    def test_wrong_amount_flagged(self):
        # 15% × 1000 = 150, but we report 200
        errors = validate_box7a([row(**{
            "BOX7A_FEDERAL TAX WITHHELD": 200.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 200.0,
        })])
        assert any("not correct amount" in r.lower() for r in reasons(errors))

    def test_nan_rate_flagged(self):
        errors = validate_box7a([row(**{"BOX3B_TAX RATE": float("nan")})])
        assert any("not valid tax rate" in r.lower() for r in reasons(errors))

    def test_rounding_applied(self):
        """round(15% × 1001) = round(150.15) = 150  →  no error."""
        errors = validate_box7a([row(**{
            "BOX2_GROSS INCOME": 1001.0,
            "BOX7A_FEDERAL TAX WITHHELD": 150.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 150.0,
        })])
        calc_errors = [e for e in errors if "not correct amount" in e[-1].lower()]
        assert calc_errors == []


# ---------------------------------------------------------------------------
# BOX10  Total Withholding Credit
# ---------------------------------------------------------------------------

class TestBOX10:

    def test_correct_sum_no_error(self):
        assert validate_box10([row(**{
            "BOX7A_FEDERAL TAX WITHHELD": 100.0,
            "BOX8_TAX WITHHELD OTHER AGENTS": 20.0,
            "BOX9_AMOUNT REPAID RECIPIENT": 5.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 125.0,
        })]) == []

    def test_wrong_sum_flagged(self):
        errors = validate_box10([row(**{
            "BOX7A_FEDERAL TAX WITHHELD": 100.0,
            "BOX8_TAX WITHHELD OTHER AGENTS": 20.0,
            "BOX9_AMOUNT REPAID RECIPIENT": 5.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 999.0,
        })])
        assert len(errors) == 1
        assert "not correct" in errors[0][-1].lower()

    def test_nan_box8_treated_as_zero(self):
        """NaN in BOX8 must be treated as 0."""
        errors = validate_box10([row(**{
            "BOX7A_FEDERAL TAX WITHHELD": 150.0,
            "BOX8_TAX WITHHELD OTHER AGENTS": float("nan"),
            "BOX9_AMOUNT REPAID RECIPIENT": 0.0,
            "BOX10_TOTAL WITHHOLDING CREDIT": 150.0,
        })])
        assert errors == []

    def test_nan_box9_treated_as_zero(self):
        """NaN in BOX9 must be treated as 0."""
        errors = validate_box10([row(**{
            "BOX7A_FEDERAL TAX WITHHELD": 150.0,
            "BOX8_TAX WITHHELD OTHER AGENTS": 0.0,
            "BOX9_AMOUNT REPAID RECIPIENT": float("nan"),
            "BOX10_TOTAL WITHHOLDING CREDIT": 150.0,
        })])
        assert errors == []

    def test_multiple_errors_all_reported(self):
        rows = [
            row(**{"BOX13A_RECIPIENT NAME1": "Good"}),
            row(**{"BOX13A_RECIPIENT NAME1": "Bad1", "BOX10_TOTAL WITHHOLDING CREDIT": 999.0}),
            row(**{"BOX13A_RECIPIENT NAME1": "Bad2", "BOX10_TOTAL WITHHOLDING CREDIT": 0.0}),
        ]
        errors = validate_box10(rows)
        names = [e[0] for e in errors]
        assert "Good" not in names
        assert "Bad1" in names
        assert "Bad2" in names


# ---------------------------------------------------------------------------
# BOX13B  Country Code / Name Match
# ---------------------------------------------------------------------------

class TestBOX13B:

    def test_matching_code_and_name_no_error(self, country_data):
        assert validate_box13b([row()], country_data) == []

    def test_mismatched_name_flagged(self, country_data):
        errors = validate_box13b(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "CA",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "France"})],
            country_data,
        )
        assert len(errors) == 1
        assert "does not match" in errors[0][-1].lower()

    def test_case_insensitive_match(self, country_data):
        errors = validate_box13b(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "ca",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "CANADA"})],
            country_data,
        )
        assert errors == []

    def test_trailing_whitespace_stripped(self, country_data):
        errors = validate_box13b(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "CA   ",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "Canada"})],
            country_data,
        )
        assert errors == []

    def test_us_code_matches_united_states(self, country_data):
        errors = validate_box13b(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "US",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "United States",
                    "BOX13D_RECIPIENT STATE(2LetterCode)": "NY",
                    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": ""})],
            country_data,
        )
        assert errors == []


# ---------------------------------------------------------------------------
# BOX13D  State / Province Code
# ---------------------------------------------------------------------------

class TestBOX13D:

    def test_us_valid_state_no_error(self, state_data, prov_data):
        errors = validate_box13d(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "US",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "United States",
                    "BOX13D_RECIPIENT STATE(2LetterCode)": "CA",
                    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": ""})],
            state_data, prov_data,
        )
        assert errors == []

    def test_us_invalid_state_flagged(self, state_data, prov_data):
        errors = validate_box13d(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "US",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "United States",
                    "BOX13D_RECIPIENT STATE(2LetterCode)": "ZZ",
                    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": ""})],
            state_data, prov_data,
        )
        assert any("state" in r.lower() for r in reasons(errors))

    def test_canada_valid_province_no_error(self, state_data, prov_data):
        assert validate_box13d([row()], state_data, prov_data) == []

    def test_canada_invalid_province_flagged(self, state_data, prov_data):
        errors = validate_box13d(
            [row(**{"BOX13D_RECIPIENT PROVINCE(2LetterCode)": "ZZ"})],
            state_data, prov_data,
        )
        assert any("province" in r.lower() or "canada" in r.lower()
                   for r in reasons(errors))

    def test_non_canada_with_province_flagged(self, state_data, prov_data):
        errors = validate_box13d(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "DE",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "Germany",
                    "BOX13D_RECIPIENT STATE(2LetterCode)": "",
                    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": "ON"})],
            state_data, prov_data,
        )
        assert any("not canada" in r.lower() for r in reasons(errors))

    def test_non_us_no_state_no_error(self, state_data, prov_data):
        errors = validate_box13d(
            [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "DE",
                    "BOX13D_RECIPIENT FOREIGN COUNTRY": "Germany",
                    "BOX13D_RECIPIENT STATE(2LetterCode)": "",
                    "BOX13D_RECIPIENT PROVINCE(2LetterCode)": ""})],
            state_data, prov_data,
        )
        state_prov_errors = [e for e in errors
                             if "state" in e[-1].lower() or "province" in e[-1].lower()]
        assert state_prov_errors == []

    def test_every_us_state_accepted(self, state_data, prov_data):
        """Every code in state_codes.json must pass for US recipients."""
        for state in state_data:
            errors = validate_box13d(
                [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "US",
                        "BOX13D_RECIPIENT FOREIGN COUNTRY": "United States",
                        "BOX13D_RECIPIENT STATE(2LetterCode)": state["Code"],
                        "BOX13D_RECIPIENT PROVINCE(2LetterCode)": ""})],
                state_data, prov_data,
            )
            state_errors = [e for e in errors if "state" in e[-1].lower()]
            assert state_errors == [], f"State {state['Code']} should be valid"

    def test_every_canadian_province_accepted(self, state_data, prov_data):
        """Every code in can_provinces.json must pass for Canadian recipients."""
        for prov in prov_data:
            errors = validate_box13d(
                [row(**{"BOX13B_RECIPIENT COUNTRY CODE": "CA",
                        "BOX13D_RECIPIENT FOREIGN COUNTRY": "Canada",
                        "BOX13D_RECIPIENT STATE(2LetterCode)": "",
                        "BOX13D_RECIPIENT PROVINCE(2LetterCode)": prov["Code"]})],
                state_data, prov_data,
            )
            prov_errors = [e for e in errors if "province" in e[-1].lower()]
            assert prov_errors == [], f"Province {prov['Code']} should be valid"
