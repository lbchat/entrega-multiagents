"""Testes do modelo de saída estruturada de recomendação."""

import pytest
from pydantic import ValidationError

from quantumfinance.agents.decision_agent import Recommendation, RecommendationOutput

VALID_FIELDS = {
    "ticker": "PETR4",
    "date": "2026-06-20",
    "recommendation": Recommendation.COMPRAR,
    "confidence": 0.8,
    "rsi": 28.5,
    "macd_signal": "bullish",
    "sentiment_score": 0.7,
    "sentiment_label": "POSITIVO",
    "top_headlines": ["Petrobras anuncia lucro recorde"],
    "reasoning": "RSI em sobrevenda e sentimento positivo.",
}


def test_recommendation_accepts_only_valid_values():
    """Valida que Recommendation aceita apenas COMPRAR, VENDER e AGUARDAR."""
    assert Recommendation("COMPRAR") == Recommendation.COMPRAR
    assert Recommendation("VENDER") == Recommendation.VENDER
    assert Recommendation("AGUARDAR") == Recommendation.AGUARDAR
    with pytest.raises(ValueError):
        Recommendation("MANTER")


def test_recommendation_output_rejects_confidence_out_of_range():
    """Valida que RecommendationOutput rejeita confidence fora de 0-1."""
    with pytest.raises(ValidationError):
        RecommendationOutput(**{**VALID_FIELDS, "confidence": 1.5})


def test_recommendation_output_rejects_invalid_date_format():
    """Valida que RecommendationOutput rejeita date fora do formato YYYY-MM-DD."""
    with pytest.raises(ValidationError):
        RecommendationOutput(**{**VALID_FIELDS, "date": "20/06/2026"})


def test_recommendation_output_accepts_valid_data():
    """Valida que dados válidos são aceitos sem erro."""
    output = RecommendationOutput(**VALID_FIELDS)
    assert output.recommendation == Recommendation.COMPRAR


def test_recommendation_output_serializes_enum_as_plain_string():
    """Valida que model_dump(mode="json") serializa o enum como string pura.

    Protege contra regressão do bug onde model_dump() simples retorna o
    membro do enum (<Recommendation.COMPRAR: 'COMPRAR'>) em vez da string
    "COMPRAR", o que corrompe a escrita em CSV via csv.DictWriter.
    """
    output = RecommendationOutput(
        ticker="PETR4",
        date="2026-06-19",
        recommendation=Recommendation.COMPRAR,
        confidence=0.75,
        rsi=28.0,
        macd_signal="bullish",
        sentiment_score=0.7,
        sentiment_label="POSITIVO",
        top_headlines=["Manchete exemplo"],
        reasoning="Teste de serialização",
    )

    serialized = output.model_dump(mode="json")

    assert isinstance(serialized["recommendation"], str), (
        f"Esperado str, obtido {type(serialized['recommendation'])}"
    )
    assert serialized["recommendation"] == "COMPRAR", (
        f"Esperado 'COMPRAR', obtido {serialized['recommendation']!r}"
    )
