"""Cliente GDELT via Google BigQuery para sentimento histórico de notícias no backtest."""

import pandas as pd
from google.cloud import bigquery

from quantumfinance.data.news_data import TICKER_KEYWORDS

NEUTRAL_FALLBACK = {
    "sentiment_score": 0.5,
    "sentiment_label": "NEUTRO",
    "news_count": 0,
    "source": "gdelt",
}

BIGQUERY_PROJECT_ID = "entrega-multi-agents"
GKG_TABLE = "gdelt-bq.gdeltv2.gkg_partitioned"

# _PARTITIONTIME particiona por dia de ingestão e permite o BigQuery podar a
# tabela (21+ TB no total) sem escanear tudo; o filtro em DATE garante a
# precisão do período pedido dentro dos dias selecionados pela partição.
QUERY = f"""
SELECT
    AVG(SAFE_CAST(SPLIT(V2Tone, ",")[OFFSET(0)] AS FLOAT64)) AS avg_tone,
    COUNT(*) AS news_count
FROM `{GKG_TABLE}`
WHERE _PARTITIONTIME BETWEEN TIMESTAMP(@partition_start) AND TIMESTAMP(@partition_end)
  AND DATE BETWEEN @date_start AND @date_end
  AND EXISTS (
    SELECT 1 FROM UNNEST(@keywords) AS kw WHERE AllNames LIKE CONCAT("%", kw, "%")
  )
"""

_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    """Reutiliza um único Client entre chamadas (criar um novo custa ~2s de autenticação)."""
    global _client
    if _client is None:
        _client = bigquery.Client(project=BIGQUERY_PROJECT_ID)
    return _client


def _label_from_score(score: float) -> str:
    """Classifica o score normalizado em POSITIVO, NEGATIVO ou NEUTRO."""
    if score > 0.6:
        return "POSITIVO"
    if score < 0.4:
        return "NEGATIVO"
    return "NEUTRO"


def fetch_gdelt_sentiment(
    ticker: str,
    date: str,
    window_days: int = 3,
) -> dict:
    """Busca sentimento histórico de notícias via GDELT (BigQuery) para o ticker, no período [date - window_days, date].

    Nunca levanta exceção: qualquer erro de rede/API/auth retorna o fallback neutro.
    """
    try:
        keywords = TICKER_KEYWORDS.get(ticker, [ticker])
        end_date = pd.Timestamp(date)
        start_date = end_date - pd.Timedelta(days=window_days)

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "partition_start", "DATE", start_date.date()
                ),
                bigquery.ScalarQueryParameter("partition_end", "DATE", end_date.date()),
                bigquery.ScalarQueryParameter(
                    "date_start", "INT64", int(start_date.strftime("%Y%m%d") + "000000")
                ),
                bigquery.ScalarQueryParameter(
                    "date_end", "INT64", int(end_date.strftime("%Y%m%d") + "235959")
                ),
                bigquery.ArrayQueryParameter("keywords", "STRING", keywords),
            ]
        )

        client = _get_client()
        rows = list(client.query(QUERY, job_config=job_config).result())

        news_count = int(rows[0]["news_count"]) if rows else 0
        avg_tone = rows[0]["avg_tone"] if rows else None

        if news_count == 0 or avg_tone is None:
            return dict(NEUTRAL_FALLBACK)

        sentiment_score = max(0.0, min(1.0, (avg_tone + 10) / 20))

        return {
            "sentiment_score": round(sentiment_score, 4),
            "sentiment_label": _label_from_score(sentiment_score),
            "news_count": news_count,
            "source": "gdelt",
        }
    except Exception:
        return dict(NEUTRAL_FALLBACK)
