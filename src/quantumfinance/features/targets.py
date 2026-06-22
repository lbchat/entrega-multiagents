"""Features históricas e retornos futuros para o backtest, sem look-ahead bias."""

import pandas as pd
import yfinance as yf

from quantumfinance.features.technical import calculate_indicators

IBOVESPA_TICKER = "^BVSP"


def _is_trading_day(yf_ticker: str, date: str) -> bool:
    """Confirma que `date` corresponde a um pregão real (não fim de semana nem feriado).

    `dayofweek` só descarta fins de semana — feriados da B3 (ex: Carnaval) passam
    despercebidos e fariam o yfinance "escorregar" silenciosamente para o próximo
    pregão disponível, duplicando valores entre datas de feriado consecutivas.
    """
    target_date = pd.Timestamp(date)
    try:
        probe = yf.download(
            yf_ticker,
            start=date,
            end=(target_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return False

    if probe.empty:
        return False

    return probe.index[0].strftime("%Y-%m-%d") == target_date.strftime("%Y-%m-%d")


def get_historical_features(ticker: str, date: str) -> dict | None:
    """Calcula indicadores técnicos usando apenas dados anteriores a `date` (sem look-ahead bias)."""
    target_date = pd.Timestamp(date)
    if target_date.dayofweek >= 5:
        return None  # fim de semana, não é dia útil

    yf_ticker = f"{ticker}.SA"
    if not _is_trading_day(yf_ticker, date):
        return None  # feriado — sem pregão nessa data

    start_date = target_date - pd.Timedelta(days=90)

    try:
        # end=date é exclusivo no yfinance: garante que nenhum dado de `date`
        # em diante seja usado no cálculo dos indicadores.
        data = yf.download(
            yf_ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=date,
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return None

    if data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return calculate_indicators(data)


def _compute_forward_return(yf_ticker: str, date: str, days: int) -> float | None:
    """Calcula o retorno percentual entre o preço em `date` e `days` dias úteis depois."""
    target_date = pd.Timestamp(date)
    end_date = target_date + pd.Timedelta(days=days * 2 + 5)  # margem para fins de semana/feriados

    try:
        data = yf.download(
            yf_ticker,
            start=date,
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty or len(data) <= days:
        return None

    # se `date` não foi pregão (feriado), o yfinance "escorrega" pro próximo
    # dia disponível — sem este check, datas de feriado consecutivas dariam
    # o mesmo retorno (mesmo preço inicial), como se fossem o mesmo dia.
    if data.index[0].strftime("%Y-%m-%d") != target_date.strftime("%Y-%m-%d"):
        return None

    start_price = float(data["Close"].iloc[0])
    end_price = float(data["Close"].iloc[days])
    return round((end_price - start_price) / start_price * 100, 4)


def get_forward_return(ticker: str, date: str, days: int = 5) -> float | None:
    """Retorna o retorno percentual real do ticker nos `days` dias úteis seguintes a `date`."""
    return _compute_forward_return(f"{ticker}.SA", date, days)


def get_ibovespa_return(date: str, days: int = 5) -> float | None:
    """Retorna o retorno percentual do Ibovespa nos `days` dias úteis seguintes a `date`."""
    return _compute_forward_return(IBOVESPA_TICKER, date, days)
