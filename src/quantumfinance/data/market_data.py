"""Coleta de dados de mercado via yfinance."""

import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """Coleta dados OHLCV do Yahoo Finance para o ticker informado."""
    yf_ticker = f"{ticker}.SA"  # tickers brasileiros usam sufixo .SA no Yahoo Finance
    try:
        data = yf.download(yf_ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            raise ValueError(f"Nenhum dado retornado para {ticker} ({yf_ticker})")
        # yfinance retorna MultiIndex nas colunas quando baixa 1 ticker em versões recentes
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar dados para {ticker}: {e}") from e
