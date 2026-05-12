from unittest.mock import Mock

import pandas as pd
import pytest
from dataclasses import dataclass

from agent.services.analyzer.base_financial_analyzer import BaseFinancialAnalyzer


@dataclass
class FakeFinancialRecordRow:
    id: str
    date: pd.Timestamp | None
    description: str
    amount: object
    label: str | None = None


class FakeFinancialRecordRepository:
    calls: list[str] = []
    records: list[FakeFinancialRecordRow] = []

    def __init__(self, db, file_type):
        self.db = db
        self.file_type = file_type

    def get_records(self) -> list[FakeFinancialRecordRow]:
        FakeFinancialRecordRepository.calls.append(self.file_type)
        return FakeFinancialRecordRepository.records


class DummyAnalyzer(BaseFinancialAnalyzer):
    file_type = "statement"

    def summarize(self):
        return {"ok": True}


@pytest.fixture(autouse=True)
def patch_financial_record_repository(monkeypatch):
    FakeFinancialRecordRepository.calls = []
    FakeFinancialRecordRepository.records = []

    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.FinancialRecordRepository",
        FakeFinancialRecordRepository,
    )


def test_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseFinancialAnalyzer()


def test_raw_df_reads_from_db_once():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-01-01"),
            description="Coffee",
            amount=1,
            label="Food",
        )
    ]
    db = Mock()
    analyzer = DummyAnalyzer(db)

    df1 = analyzer.raw_df
    df2 = analyzer.raw_df

    assert not df1.empty
    assert df1 is df2
    assert len(FakeFinancialRecordRepository.calls) == 1
    assert FakeFinancialRecordRepository.calls[0] == "statement"
    assert list(df1["amount"]) == [1]


def test_df_normalizes_raw_df_once():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-01-01"),
            description="Good row",
            amount="10.5",
            label="Food",
        ),
        FakeFinancialRecordRow(
            id="2",
            date=pd.Timestamp("2025-01-01"),
            description="Bad row",
            amount="bad",
            label="Food",
        ),
        FakeFinancialRecordRow(
            id="3",
            date=pd.Timestamp("2025-01-01"),
            description="Another good row",
            amount="20",
            label="Food",
        ),
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    df1 = analyzer.df
    df2 = analyzer.df

    assert df1 is df2
    assert list(df1["amount"]) == [10.5, 20.0]


def test_normalize_df_returns_copy_for_empty_df():
    db = Mock()
    analyzer = DummyAnalyzer(db)
    original = pd.DataFrame()

    result = analyzer.normalize_df(original)

    assert result.empty
    assert result is not original


def test_coerce_common_types_converts_amount_and_drops_invalid_rows():
    db = Mock()
    analyzer = DummyAnalyzer(db)
    df = pd.DataFrame(
        {
            "amount": ["12.34", "bad", None, "5"],
            "other": [1, 2, 3, 4],
        }
    )

    result = analyzer._coerce_common_types(df)

    assert list(result["amount"]) == [12.34, 5.0]
    assert list(result["other"]) == [1, 4]


def test_coerce_common_types_raises_when_amount_column_missing():
    db = Mock()
    analyzer = DummyAnalyzer(db)
    df = pd.DataFrame({"date": [pd.Timestamp("2025-01-01")]})

    with pytest.raises(KeyError):
        analyzer._coerce_common_types(df)


def test_total_days_returns_1_when_df_empty():
    FakeFinancialRecordRepository.records = []

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.total_days == 1


def test_total_days_returns_1_when_date_column_missing(monkeypatch):
    db = Mock()
    analyzer = DummyAnalyzer(db)

    monkeypatch.setattr(
        analyzer,
        "raw_df",
        pd.DataFrame({"amount": [1, 2]}),
    )

    assert analyzer.total_days == 1


def test_total_days_returns_1_when_dates_are_same():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-01-10"),
            description="A",
            amount=1,
            label=None,
        ),
        FakeFinancialRecordRow(
            id="2",
            date=pd.Timestamp("2025-01-10"),
            description="B",
            amount=2,
            label=None,
        ),
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.total_days == 1


def test_total_days_returns_date_difference_when_greater_than_one():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-01-01"),
            description="A",
            amount=1,
            label=None,
        ),
        FakeFinancialRecordRow(
            id="2",
            date=pd.Timestamp("2025-01-10"),
            description="B",
            amount=2,
            label=None,
        ),
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.total_days == 9


def test_total_days_returns_1_when_min_or_max_date_is_na():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.NaT,
            description="A",
            amount=1,
            label=None,
        )
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.total_days == 1


def test_get_date_range_uses_self_df_by_default():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-02-01"),
            description="A",
            amount=1,
            label=None,
        ),
        FakeFinancialRecordRow(
            id="2",
            date=pd.Timestamp("2025-02-05"),
            description="B",
            amount=2,
            label=None,
        ),
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.get_date_range() == {
        "start": "2025-02-01",
        "end": "2025-02-05",
    }


def test_get_date_range_accepts_override_df():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.Timestamp("2025-01-01"),
            description="A",
            amount=1,
            label=None,
        )
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)
    override = pd.DataFrame(
        {
            "amount": [1, 2],
            "date": [pd.Timestamp("2025-03-01"), pd.Timestamp("2025-03-07")],
        }
    )

    assert analyzer.get_date_range(override) == {
        "start": "2025-03-01",
        "end": "2025-03-07",
    }


def test_get_date_range_returns_none_for_empty_or_missing_date():
    FakeFinancialRecordRepository.records = []

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.get_date_range() == {"start": None, "end": None}
    assert analyzer.get_date_range(pd.DataFrame({"amount": [1]})) == {
        "start": None,
        "end": None,
    }


def test_get_date_range_returns_none_when_dates_are_nat():
    FakeFinancialRecordRepository.records = [
        FakeFinancialRecordRow(
            id="1",
            date=pd.NaT,
            description="A",
            amount=1,
            label=None,
        )
    ]

    db = Mock()
    analyzer = DummyAnalyzer(db)

    assert analyzer.get_date_range() == {"start": None, "end": None}


def test_llm_answer_appends_context_and_calls_model(monkeypatch):
    captured = {}

    def fake_call_model(question, history):
        captured["question"] = question
        captured["history"] = history
        return "model response"

    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.call_model",
        fake_call_model,
    )

    db = Mock()
    analyzer = DummyAnalyzer(db)
    history = [{"role": "user", "content": "previous"}]

    result = analyzer.llm_answer(
        question="What happened?",
        history=history,
        context="Here is the context",
    )

    assert result == "model response"
    assert captured["question"] == "What happened?"
    assert captured["history"] == [
        {"role": "user", "content": "previous"},
        {"role": "assistant", "content": "Here is the context"},
    ]
    assert history == [{"role": "user", "content": "previous"}]


def test_llm_answer_handles_none_history(monkeypatch):
    def fake_call_model(question, history):
        assert question == "Q"
        assert history == [{"role": "assistant", "content": "CTX"}]
        return "ok"

    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.call_model",
        fake_call_model,
    )

    db = Mock()
    analyzer = DummyAnalyzer(db)

    result = analyzer.llm_answer(
        question="Q",
        history=None,
        context="CTX",
    )

    assert result == "ok"