"""Roda o backtest com sentimento histórico via GDELT/BigQuery (Etapa 6.5, Tarefa 5).

90 dias completos, alinhado ao backtest base (Etapa 6): o BigQuery não tem
o rate limit informal da API REST do GDELT, então não há mais necessidade
de reduzir a amostra.
"""

from datetime import date, timedelta

from quantumfinance.backtesting.strategy import run_backtest
from quantumfinance.universe import TICKERS

end = date.today().strftime("%Y-%m-%d")
start = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")

df = run_backtest(
    tickers=TICKERS,
    start_date=start,
    end_date=end,
    output_path="data/backtest_results_gdelt.csv",
    use_gdelt=True,
)
print(f"Backtest concluido: {len(df)} registros")
print(df[["date", "ticker", "recommendation", "sentiment_score", "sentiment_source"]].head(20))
