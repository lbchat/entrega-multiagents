from quantumfinance.features.targets import (
    get_historical_features,
    get_forward_return,
    get_ibovespa_return,
)
from quantumfinance.tools.decision_tools import apply_decision_rules

date = "2026-03-03"
ticker = "PETR4"

features = get_historical_features(ticker, date)
print("Features:", features)

forward = get_forward_return(ticker, date, days=5)
print("Retorno 5d:", forward)

ibov = get_ibovespa_return(date, days=5)
print("Ibovespa 5d:", ibov)

if features:
    decision = apply_decision_rules(
        rsi=features["rsi"],
        macd_signal=features["macd_signal"],
        sentiment_score=0.5,
    )
    print("Decisão:", decision)
