"""Módulo de persistência de recomendações em CSV."""

import csv
from pathlib import Path

RECOMMENDATIONS_PATH = Path("data/recommendations.csv")

FIELDNAMES = [
    "ticker", "date", "recommendation", "confidence",
    "rsi", "macd_signal", "sentiment_score", "sentiment_label",
    "top_headlines", "reasoning",
]


def save_recommendation(data: dict) -> None:
    """Persiste uma recomendação no CSV histórico."""
    RECOMMENDATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not RECOMMENDATIONS_PATH.exists()

    with open(RECOMMENDATIONS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(data)


def load_recommendations() -> list[dict]:
    """Carrega o histórico de recomendações do CSV."""
    if not RECOMMENDATIONS_PATH.exists():
        return []
    with open(RECOMMENDATIONS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
