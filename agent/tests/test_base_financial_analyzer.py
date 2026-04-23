import pandas as pd
import pytest

from agent.services.analyzer.base_financial_analyzer import BaseFinancialAnalyzer


class DummyAnalyzer(BaseFinancialAnalyzer):
    worksheet_name = "test_sheet"

    def summarize(self):
        return {"ok": True}


def test_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseFinancialAnalyzer()


def test_raw_df_reads_from_google_sheets_once(monkeypatch):
    calls = []

    def fake_read_transactions_df(*, spreadsheet_name, worksheet_name):
        calls.append((spreadsheet_name, worksheet_name))
        return pd.DataFrame({"amount": [1], "date": [pd.Timestamp("2025-01-01")]})

    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        fake_read_transactions_df,
    )

    analyzer = DummyAnalyzer()

    df1 = analyzer.raw_df
    df2 = analyzer.raw_df

    assert not df1.empty
    assert df1 is df2
    assert len(calls) == 1
    assert calls[0][1] == "test_sheet"


def test_df_normalizes_raw_df_once(monkeypatch):
    raw = pd.DataFrame(
        {
            "amount": ["10.5", "bad", "20"],
            "date": [pd.Timestamp("2025-01-01")] * 3,
        }
    )

    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: raw,
    )

    analyzer = DummyAnalyzer()

    df1 = analyzer.df
    df2 = analyzer.df

    assert df1 is df2
    assert list(df1["amount"]) == [10.5, 20.0]


def test_normalize_df_returns_copy_for_empty_df():
    analyzer = DummyAnalyzer()
    original = pd.DataFrame()

    result = analyzer.normalize_df(original)

    assert result.empty
    assert result is not original


def test_coerce_common_types_converts_amount_and_drops_invalid_rows():
    analyzer = DummyAnalyzer()
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
    analyzer = DummyAnalyzer()
    df = pd.DataFrame({"date": [pd.Timestamp("2025-01-01")]})

    with pytest.raises(KeyError):
        analyzer._coerce_common_types(df)


def test_total_days_returns_1_when_df_empty(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.total_days == 1


def test_total_days_returns_1_when_date_column_missing(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame({"amount": [1, 2]}),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.total_days == 1


def test_total_days_returns_1_when_dates_are_same(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1, 2],
                "date": [pd.Timestamp("2025-01-10"), pd.Timestamp("2025-01-10")],
            }
        ),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.total_days == 1


def test_total_days_returns_date_difference_when_greater_than_one(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1, 2],
                "date": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-10")],
            }
        ),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.total_days == 9


def test_total_days_returns_1_when_min_or_max_date_is_na(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1],
                "date": [pd.NaT],
            }
        ),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.total_days == 1


def test_get_date_range_uses_self_df_by_default(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1, 2],
                "date": [pd.Timestamp("2025-02-01"), pd.Timestamp("2025-02-05")],
            }
        ),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.get_date_range() == {
        "start": "2025-02-01",
        "end": "2025-02-05",
    }


def test_get_date_range_accepts_override_df(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1],
                "date": [pd.Timestamp("2025-01-01")],
            }
        ),
    )

    analyzer = DummyAnalyzer()
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


def test_get_date_range_returns_none_for_empty_or_missing_date(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(),
    )

    analyzer = DummyAnalyzer()

    assert analyzer.get_date_range() == {"start": None, "end": None}
    assert analyzer.get_date_range(pd.DataFrame({"amount": [1]})) == {
        "start": None,
        "end": None,
    }


def test_get_date_range_returns_none_when_dates_are_nat(monkeypatch):
    monkeypatch.setattr(
        "agent.services.analyzer.base_financial_analyzer.read_transactions_df",
        lambda **kwargs: pd.DataFrame(
            {
                "amount": [1],
                "date": [pd.NaT],
            }
        ),
    )

    analyzer = DummyAnalyzer()

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

    analyzer = DummyAnalyzer()
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

    analyzer = DummyAnalyzer()

    result = analyzer.llm_answer(
        question="Q",
        history=None,
        context="CTX",
    )

    assert result == "ok"