"""Métricas de avaliação do backtest."""

import pandas as pd

AGUARDAR_NEUTRAL_THRESHOLD = 2.0  # |retorno| abaixo disso conta como acerto para AGUARDAR


def _is_hit(recommendation: str, forward_return: float) -> bool:
    """Valida se a recomendação bateu com a direção real do retorno."""
    if recommendation == "COMPRAR":
        return forward_return > 0
    if recommendation == "VENDER":
        return forward_return < 0
    return abs(forward_return) < AGUARDAR_NEUTRAL_THRESHOLD  # AGUARDAR


def calculate_metrics(results: pd.DataFrame) -> dict:
    """Calcula métricas de avaliação a partir dos resultados do backtest."""
    valid = results.dropna(subset=["forward_return_5d"])
    beat_ibov_valid = results.dropna(subset=["beat_ibov"])

    accuracy = None
    if not valid.empty:
        hits = valid.apply(lambda row: _is_hit(row["recommendation"], row["forward_return_5d"]), axis=1)
        accuracy = round(float(hits.mean()), 4)

    beat_ibov_rate = None
    if not beat_ibov_valid.empty:
        beat_ibov_rate = round(float(beat_ibov_valid["beat_ibov"].mean()), 4)

    buy_returns = valid.loc[valid["recommendation"] == "COMPRAR", "forward_return_5d"]
    sell_returns = valid.loc[valid["recommendation"] == "VENDER", "forward_return_5d"]

    avg_return_on_buy = round(float(buy_returns.mean()), 4) if not buy_returns.empty else None
    avg_return_on_sell = round(float(sell_returns.mean()), 4) if not sell_returns.empty else None

    recommendation_counts = results["recommendation"].value_counts().to_dict()

    sharpe_proxy = None
    if len(valid) > 1:
        std = valid["forward_return_5d"].std()
        if pd.notna(std) and std != 0:
            sharpe_proxy = round(float(valid["forward_return_5d"].mean() / std), 4)

    return {
        "accuracy": accuracy,
        "beat_ibov_rate": beat_ibov_rate,
        "avg_return_on_buy": avg_return_on_buy,
        "avg_return_on_sell": avg_return_on_sell,
        "recommendation_counts": recommendation_counts,
        "sharpe_proxy": sharpe_proxy,
    }
