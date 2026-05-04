import pytest

from agent.models.pdf_models import LineSchema, TransactionRow
from agent.services.parser.base_pdf_parser import BasePdfParser


TEST_SCHEMA = LineSchema(
    name="date_description_amount",
    columns=["date", "description", "amount"],
    min_parts=3,
    start_markers=[],
    end_markers=[],
    credit=True,
)


class DummyPdfParser(BasePdfParser):
    def __init__(self):
        super().__init__()
    
    schema = TEST_SCHEMA


class FakePage:
    def __init__(self, text=None):
        self._text = text

    def extract_text(self):
        return self._text


def test_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BasePdfParser(TEST_SCHEMA)


def test_build_base_result():
    parser = DummyPdfParser()

    assert parser.build_base_result() == {
        "pages": [],
        "tables": [],
        "data": [],
        "full_text": "",
    }


def test_process_page_returns_text_page_and_data():
    parser = DummyPdfParser()
    page = FakePage(text="01/01 Starbucks 5.00")

    result = parser.process_page(2, page, 2)
    row = result["data"][0]
    
    assert isinstance(row, TransactionRow)
    assert row.date == "01/01"
    assert row.description == "Starbucks"
    assert row.amount == 5.00
    assert row.label == ""
    assert row.id


def test_process_page_uses_empty_string_when_extract_text_returns_none():
    parser = DummyPdfParser()
    page = FakePage(text=None)

    result = parser.process_page(1, page, 1)

    assert result["full_text"] == ""
    assert result["page"] == {
        "page_number": 1,
        "text": "",
    }
    assert result["data"] == []