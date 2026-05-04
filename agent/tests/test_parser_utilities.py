import pytest

from agent.models.pdf_models import LineSchema
from agent.services.parser.parser_utilities import (
    extract_statement_years,
    is_account_number,
    is_date_token,
    normalize_date_value,
    parse_amount,
)


TRANSACTION_SCHEMA = LineSchema(
    name="date_description_amount",
    columns=["date", "description", "amount"],
    min_parts=3,
    start_markers=[],
    end_markers=["Total"],
    credit=False,
)

BANK_SCHEMA = LineSchema(
    name="date_description_amount",
    columns=["date", "description", "amount"],
    min_parts=3,
    start_markers=[],
    end_markers=["Total deposits"],
    credit=False,
)

BOA_CREDIT_SCHEMA = LineSchema(
    name="transaction_posting_description_ref_account_amount_total",
    columns=[
        "transaction_date",
        "posting_date",
        "description",
        "reference_number",
        "account_number",
        "amount",
        "total",
    ],
    min_parts=6,
    start_markers=[],
    end_markers=[],
    credit=True,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("01/15", True),
        ("1/5/2025", True),
        ("2025-01-15", True),
        ("Jan 5", True),
        (" not-a-date ", False),
        ("01-15", False),
    ],
)
def test_is_date_token(value, expected):
    assert is_date_token(value) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$1,234.56", 1234.56),
        ("(123.45)", -123.45),
        ("123.45-", -123.45),
        (" 99.01 ", 99.01),
        ("$0.00", 0.0),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


def test_parse_amount_raises_for_invalid_value():
    with pytest.raises(ValueError):
        parse_amount("abc")


def test_normalize_date_value_returns_original_when_missing_inputs():
    assert normalize_date_value(None, (1, 2025, 1, 2025)) is None
    assert normalize_date_value("01/15", None) == "01/15"
    assert normalize_date_value("2025-01-15", (1, 2025, 1, 2025)) == "2025-01-15"


def test_normalize_date_value_mmdd_same_year():
    assert normalize_date_value("01/15", (1, 2025, 1, 2025)) == "2025-01-15"


def test_normalize_date_value_cross_year_uses_start_year_for_later_month():
    assert normalize_date_value("12/31", (12, 2024, 1, 2025)) == "2024-12-31"


def test_normalize_date_value_cross_year_uses_end_year_for_earlier_month():
    assert normalize_date_value("01/01", (12, 2024, 1, 2025)) == "2025-01-01"


def test_normalize_date_value_raises_for_invalid_date():
    with pytest.raises(ValueError):
        normalize_date_value("hello", (1, 2025, 1, 2025))


def test_extract_statement_years_returns_none_for_empty_or_no_match():
    assert extract_statement_years(None) is None
    assert extract_statement_years("") is None
    assert extract_statement_years("hello world") is None


def test_extract_statement_years_with_explicit_start_year():
    text = "Statement period January 15, 2024 to February 14, 2025"

    assert extract_statement_years(text) == (1, 2024, 2, 2025)


def test_extract_statement_years_infers_same_year_when_start_year_missing():
    text = "January 15 to February 14, 2025"

    assert extract_statement_years(text) == (1, 2025, 2, 2025)


def test_extract_statement_years_infers_previous_year_when_cross_year():
    text = "December 15 to January 14, 2025"

    assert extract_statement_years(text) == (12, 2024, 1, 2025)
    

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1234", True),
        ("0000", True),
        ("123", False),
        ("12345", False),
        ("abcd", False),
    ],
)
def test_is_account_number(value, expected):
    assert is_account_number(value) is expected