"""Runner do backtest histórico com lógica de decisão determinística (sem LLM)."""

from pathlib import Path

import pandas as pd

from quantumfinance.data.gdelt_client import fetch_gdelt_sentiment
from quantumfinance.features.targets import (
    get_forward_return,
    get_historical_features,
    get_ibovespa_return,
)
from quantumfinance.tools.decision_tools import apply_decision_rules

RESULT_COLUMNS = [
    "date", "ticker", "recommendation", "confidence", "rsi", "macd_signal",
    "sentiment_score", "sentiment_source", "forward_return_5d", "ibovespa_return_5d", "beat_ibov",
]

PLACEHOLDER_SENTIMENT_SCORE = 0.5  # sentimento neutro usado quando o GDELT está desativado


def run_backtest(
    tickers: list[str],
    start_date: str,
    end_date: str,
    output_path: str = "data/backtest_results.csv",
    use_gdelt: bool = True,
) -> pd.DataFrame:
    """Roda o backtest histórico para os tickers informados, sem chamadas de LLM.

    Com `use_gdelt=True`, busca sentimento histórico real via GDELT
    (`fetch_gdelt_sentiment`); com `use_gdelt=False`, usa sentimento neutro
    fixo (comportamento original, sem chamadas externas extras).
    """
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

            if use_gdelt:
                sentiment = fetch_gdelt_sentiment(ticker, date_str)
                sentiment_score = sentiment["sentiment_score"]
                sentiment_source = "gdelt"
            else:
                sentiment_score = PLACEHOLDER_SENTIMENT_SCORE
                sentiment_source = "placeholder"

            decision = apply_decision_rules(
                rsi=features["rsi"],
                macd_signal=features["macd_signal"],
                sentiment_score=sentiment_score,
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
                "sentiment_score": sentiment_score,
                "sentiment_source": sentiment_source,
                "forward_return_5d": forward_return,
                "ibovespa_return_5d": ibovespa_return,
                "beat_ibov": beat_ibov,
            })

    results = pd.DataFrame(rows, columns=RESULT_COLUMNS)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_file, index=False)

    return results
