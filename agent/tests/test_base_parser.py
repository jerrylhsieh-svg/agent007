import pytest

from agent.services.parser.base_pdf_parser import BasePdfParser


class DummyPdfParser(BasePdfParser):
    def __init__(self):
        self.normalize_calls = []

    def  _extract_from_page(self, page: str) -> list:
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue
        return page.splitlines()

    def _normalize_date(self, record=None, statement_period=None) -> None:
        self.normalize_calls.append((record, statement_period))


class FakePage:
    def __init__(self, text=None, tables=None):
        self._text = text
        self._tables = tables or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


def test_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BasePdfParser()


def test_build_base_result():
    parser = DummyPdfParser()

    result = parser.build_base_result()

    assert result == {
        "pages": [],
        "tables": [],
        "data": [],
        "full_text": "",
    }


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
    parser = DummyPdfParser()
    assert parser._is_date_token(value) is expected


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
    parser = DummyPdfParser()
    assert parser._parse_amount(raw) == expected


def test_parse_amount_raises_for_invalid_value():
    parser = DummyPdfParser()

    with pytest.raises(ValueError):
        parser._parse_amount("abc")


def test_normalize_date_value_returns_original_when_missing_inputs():
    parser = DummyPdfParser()

    assert parser._normalize_date_value(None, (1, 2025, 1, 2025)) is None
    assert parser._normalize_date_value("01/15", None) == "01/15"


def test_normalize_date_value_delegates_to_normalize_mmdd():
    parser = DummyPdfParser()

    result = parser._normalize_date_value("01/15", (1, 2025, 1, 2025))

    assert result == "2025-01-15"


def test_extract_statement_years_returns_none_for_empty_or_no_match():
    parser = DummyPdfParser()

    assert parser._extract_statement_years(None) is None
    assert parser._extract_statement_years("") is None
    assert parser._extract_statement_years("hello world") is None


def test_extract_statement_years_with_explicit_start_year():
    parser = DummyPdfParser()

    text = "Statement period January 15, 2024 to February 14, 2025"
    result = parser._extract_statement_years(text)

    assert result == (1, 2024, 2, 2025)


def test_extract_statement_years_infers_same_year_when_start_year_missing():
    parser = DummyPdfParser()

    text = "January 15 to February 14, 2025"
    result = parser._extract_statement_years(text)

    assert result == (1, 2025, 2, 2025)


def test_extract_statement_years_infers_previous_year_when_cross_year():
    parser = DummyPdfParser()

    text = "December 15 to January 14, 2025"
    result = parser._extract_statement_years(text)

    assert result == (12, 2024, 1, 2025)



def test_extract_tables_formats_each_table_with_page_metadata():
    parser = DummyPdfParser()
    page = FakePage(
        text="irrelevant",
        tables=[
            [["a", "b"], ["1", "2"]],
            [["x", "y"]],
        ],
    )

    result = parser._extract_tables(page, 3)

    assert result == [
        {
            "page_number": 3,
            "table_index": 1,
            "rows": [["a", "b"], ["1", "2"]],
        },
        {
            "page_number": 3,
            "table_index": 2,
            "rows": [["x", "y"]],
        },
    ]


def test_process_page_returns_text_page_tables_and_data(monkeypatch):
    parser = DummyPdfParser()
    page = FakePage(
        text="SECTION: Deposits\nline one",
        tables=[[["col1", "col2"]]],
    )

    monkeypatch.setattr(
        parser,
        "_extract_from_page",
        lambda page_text: [{"parsed": page_text}],
    )
    monkeypatch.setattr(
        parser,
        "_extract_tables",
        lambda page_obj, page_number: [{"page_number": page_number, "rows": [["t"]]}],
    )

    result = parser.process_page(2, page)

    assert result == {
        "full_text": "SECTION: Deposits\nline one",
        "page": {
            "page_number": 2,
            "text": "SECTION: Deposits\nline one",
        },
        "tables": [{"page_number": 2, "rows": [["t"]]}],
        "data": [{"parsed": "SECTION: Deposits\nline one"}],
    }


def test_process_page_uses_empty_string_when_extract_text_returns_none(monkeypatch):
    parser = DummyPdfParser()
    page = FakePage(text=None, tables=[])

    monkeypatch.setattr(parser, "_extract_from_page", lambda page_text: [])
    monkeypatch.setattr(parser, "_extract_tables", lambda page_obj, page_number: [])

    result = parser.process_page(1, page)

    assert result["full_text"] == ""
    assert result["page"] == {"page_number": 1, "text": ""}
