"""Tools de sentimento registradas no SentimentAgent."""

from langchain_core.tools import tool
from quantumfinance.data.news_data import fetch_news
from quantumfinance.features.sentiment import aggregate_sentiment


@tool
def get_sentiment_features(ticker: str) -> dict:
    """Retorna sentimento agregado das notícias recentes para o ticker informado."""
    news = fetch_news(ticker)
    return aggregate_sentiment(news)
