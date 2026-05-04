import pytest

from agent.models.pdf_models import LineSchema
from agent.services.parser.base_pdf_parser import BasePdfParser


TEST_SCHEMA = LineSchema(
    name="date_description_amount",
    columns=["date", "description", "amount"],
    min_parts=3,
    start_markers=[],
    end_markers=[],
    credit=False,
)


class DummyPdfParser(BasePdfParser):
    def __init__(self):
        super().__init__()

    def _extract_from_page(self, page: str) -> list:
        return [{"parsed": page}]


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

    result = parser.process_page(2, page)

    assert result == {
        "full_text": "01/01 Starbucks 5.00",
        "page": {
            "page_number": 2,
            "text": "01/01 Starbucks 5.00",
        },
        "data": [{"parsed": "01/01 Starbucks 5.00"}],
    }


def test_process_page_uses_empty_string_when_extract_text_returns_none():
    parser = DummyPdfParser()
    page = FakePage(text=None)

    result = parser.process_page(1, page)

    assert result["full_text"] == ""
    assert result["page"] == {
        "page_number": 1,
        "text": "",
    }
    assert result["data"] == [{"parsed": ""}]