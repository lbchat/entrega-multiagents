"""Testes de persistência de recomendações em CSV."""

import quantumfinance.output.storage as storage

SAMPLE_RECOMMENDATION = {
    "ticker": "PETR4",
    "date": "2026-06-20",
    "recommendation": "COMPRAR",
    "confidence": 0.75,
    "rsi": 27.5,
    "macd_signal": "bearish",
    "sentiment_score": 0.94,
    "sentiment_label": "POSITIVO",
    "top_headlines": ["Manchete exemplo"],
    "reasoning": "Teste de persistência",
}


def test_save_recommendation_creates_file_if_missing(tmp_path, monkeypatch):
    """Valida que save_recommendation cria o arquivo se não existir."""
    csv_path = tmp_path / "recommendations.csv"
    monkeypatch.setattr(storage, "RECOMMENDATIONS_PATH", csv_path)

    assert not csv_path.exists()
    storage.save_recommendation(SAMPLE_RECOMMENDATION)
    assert csv_path.exists()


def test_save_recommendation_appends_without_overwriting(tmp_path, monkeypatch):
    """Valida que save_recommendation adiciona linha sem sobrescrever existentes."""
    csv_path = tmp_path / "recommendations.csv"
    monkeypatch.setattr(storage, "RECOMMENDATIONS_PATH", csv_path)

    storage.save_recommendation(SAMPLE_RECOMMENDATION)
    storage.save_recommendation({**SAMPLE_RECOMMENDATION, "ticker": "VALE3"})

    rows = storage.load_recommendations()
    assert len(rows) == 2
    assert rows[0]["ticker"] == "PETR4"
    assert rows[1]["ticker"] == "VALE3"


def test_load_recommendations_returns_empty_list_if_file_missing(tmp_path, monkeypatch):
    """Valida que load_recommendations retorna lista vazia se arquivo não existir."""
    csv_path = tmp_path / "recommendations.csv"
    monkeypatch.setattr(storage, "RECOMMENDATIONS_PATH", csv_path)

    assert storage.load_recommendations() == []
