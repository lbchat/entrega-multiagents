"""Runner do backtest histórico com lógica de decisão determinística (sem LLM)."""

from pathlib import Path

import pandas as pd

from quantumfinance.features.targets import (
    get_forward_return,
    get_historical_features,
    get_ibovespa_return,
)
from quantumfinance.tools.decision_tools import apply_decision_rules

RESULT_COLUMNS = [
    "date", "ticker", "recommendation", "confidence", "rsi", "macd_signal",
    "sentiment_score", "forward_return_5d", "ibovespa_return_5d", "beat_ibov",
]

HISTORICAL_SENTIMENT_SCORE = 0.5  # sentimento real não está disponível para datas passadas


def run_backtest(
    tickers: list[str],
    start_date: str,
    end_date: str,
    output_path: str = "data/backtest_results.csv",
) -> pd.DataFrame:
    """Roda o backtest histórico para os tickers informados, sem chamadas de LLM."""
    business_days = pd.bdate_range(start_date, end_date)
    rows = []

    for date in business_days:
        date_str = date.strftime("%Y-%m-%d")
        # o Ibovespa não depende do ticker: calcula uma vez por dia, não uma vez por ticker
        ibovespa_return = get_ibovespa_return(date_str)

        for ticker in tickers:
            features = get_historical_features(ticker, date_str)
            if features is None:
                continue

            decision = apply_decision_rules(
                rsi=features["rsi"],
                macd_signal=features["macd_signal"],
                sentiment_score=HISTORICAL_SENTIMENT_SCORE,
            )

            forward_return = get_forward_return(ticker, date_str)

            if forward_return is None or ibovespa_return is None:
                beat_ibov = None
            else:
                beat_ibov = forward_return > ibovespa_return

            rows.append({
                "date": date_str,
                "ticker": ticker,
                "recommendation": decision["recommendation"],
                "confidence": decision["confidence"],
                "rsi": features["rsi"],
                "macd_signal": features["macd_signal"],
                "sentiment_score": HISTORICAL_SENTIMENT_SCORE,
                "forward_return_5d": forward_return,
                "ibovespa_return_5d": ibovespa_return,
                "beat_ibov": beat_ibov,
            })

    results = pd.DataFrame(rows, columns=RESULT_COLUMNS)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_file, index=False)

    return results
