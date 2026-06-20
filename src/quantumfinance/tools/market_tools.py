"""Tools de mercado registradas no MarketAgent."""

from langchain_core.tools import tool
from quantumfinance.data.market_data import fetch_ohlcv
from quantumfinance.features.technical import calculate_indicators


@tool
def get_market_features(ticker: str) -> dict:
    """Retorna preço atual e indicadores técnicos (RSI, MACD, médias móveis, Bollinger) para o ticker informado."""
    data = fetch_ohlcv(ticker)
    return calculate_indicators(data)
