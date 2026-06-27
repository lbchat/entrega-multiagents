"""Tool de análise contextual por esferas temáticas, registrada no ContextRouterAgent."""

from langchain_core.tools import tool

from quantumfinance.context.router import get_context_keywords, route_context_search
from quantumfinance.data.news_data import fetch_news
from quantumfinance.features.sentiment import aggregate_sentiment

NEUTRAL_OVERALL_SENTIMENT = 0.5  # usado quando nenhuma esfera tem notícias


@tool
def analyze_context(ticker: str) -> dict:
    """Analisa o contexto por esferas temáticas para o ticker informado."""
    news = fetch_news(ticker)
    news_by_sphere = route_context_search(ticker, news)

    sphere_sentiment = {}
    for sphere, sphere_news in news_by_sphere.items():
        aggregated = aggregate_sentiment(sphere_news)
        sphere_sentiment[sphere] = {
            "sentiment_label": aggregated["sentiment_label"],
            "sentiment_score": aggregated["sentiment_score"],
            "news_count": aggregated["news_count"],
            "headlines": aggregated["top_headlines"],
        }

    dominant_sphere = None
    overall_sentiment = NEUTRAL_OVERALL_SENTIMENT
    total_news = sum(data["news_count"] for data in sphere_sentiment.values())

    if sphere_sentiment:
        dominant_sphere = max(sphere_sentiment, key=lambda s: sphere_sentiment[s]["news_count"])

    if total_news > 0:
        weighted_sum = sum(
            data["sentiment_score"] * data["news_count"] for data in sphere_sentiment.values()
        )
        overall_sentiment = round(weighted_sum / total_news, 4)

    result = {
        "ticker": ticker,
        "spheres_analyzed": list(sphere_sentiment.keys()),
        "sphere_sentiment": sphere_sentiment,
        "dominant_sphere": dominant_sphere,
        "overall_sentiment": overall_sentiment,
    }

    if not sphere_sentiment:
        result["monitored_spheres"] = list(get_context_keywords(ticker).keys())

    return result
