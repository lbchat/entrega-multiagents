"""Testa o agente para todos os tickers monitorados."""
import time

from quantumfinance.agents.orchestrator import ask
from quantumfinance.universe import TICKERS

for ticker in TICKERS:
    print(f"\n{'=' * 50}")
    print(f"TESTANDO: {ticker}")
    print('=' * 50)
    try:
        response = ask(f"Qual a recomendação para {ticker} hoje?")
        print(response)
        print(f"OK: {ticker}")
    except Exception as e:
        print(f"FALHOU: {ticker}: {e}")
    time.sleep(2)  # pausa entre chamadas para não sobrecarregar a API

print("\n\nResumo: verifique data/recommendations.csv")
