from datetime import date

from langchain_core.tools import tool

from quantumfinance.agents.decision_agent import Recommendation, RecommendationOutput
from quantumfinance.tools.market_tools import get_market_features
from quantumfinance.tools.news_tools import get_sentiment_features


@tool
def generate_recommendation(ticker: str) -> dict:
    """Gera recomendação fundamentada de COMPRAR, VENDER ou AGUARDAR para o ticker informado."""
    market = get_market_features.invoke({"ticker": ticker})
    sentiment = get_sentiment_features.invoke({"ticker": ticker})

    rsi = market.get("rsi", 50.0)
    macd_signal = market.get("macd_signal", "neutro")
    sentiment_score = sentiment.get("sentiment_score", 0.0)
    sentiment_label = sentiment.get("sentiment_label", "NEUTRO")
    top_headlines = sentiment.get("top_headlines", [])

    # Lógica de decisão baseada em regras interpretáveis
    bullish_signals = 0
    bearish_signals = 0

    if rsi < 30:
        bullish_signals += 2  # sobrevenda forte
    elif rsi < 45:
        bullish_signals += 1
    elif rsi > 70:
        bearish_signals += 2  # sobrecompra forte
    elif rsi > 55:
        bearish_signals += 1

    if macd_signal == "bullish":
        bullish_signals += 1
    elif macd_signal == "bearish":
        bearish_signals += 1

    if sentiment_score > 0.6:
        bullish_signals += 1
    elif sentiment_score < 0.4:
        bearish_signals += 1

    total = bullish_signals + bearish_signals
    if total == 0:
        recommendation = Recommendation.AGUARDAR
        confidence = 0.5
    elif bullish_signals > bearish_signals:
        recommendation = Recommendation.COMPRAR
        confidence = round(bullish_signals / total, 2)
    elif bearish_signals > bullish_signals:
        recommendation = Recommendation.VENDER
        confidence = round(bearish_signals / total, 2)
    else:
        recommendation = Recommendation.AGUARDAR
        confidence = 0.5

    reasoning = (
        f"RSI em {rsi:.1f} ({'sobrevenda' if rsi < 30 else 'sobrecompra' if rsi > 70 else 'neutro'}). "
        f"MACD {macd_signal}. "
        f"Sentimento {sentiment_label} (score: {sentiment_score:.2f}). "
        f"Sinais altistas: {bullish_signals}, baixistas: {bearish_signals}."
    )

    output = RecommendationOutput(
        ticker=ticker,
        date=date.today().isoformat(),
        recommendation=recommendation,
        confidence=confidence,
        rsi=rsi,
        macd_signal=macd_signal,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        top_headlines=top_headlines[:3],
        reasoning=reasoning,
    )

    return output.model_dump(mode="json")
