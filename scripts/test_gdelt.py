from quantumfinance.data.gdelt_client import fetch_gdelt_sentiment

# Testa com data recente (dentro dos 3 meses garantidos)
result = fetch_gdelt_sentiment("PETR4", "2026-06-01", window_days=3)
print("Resultado PETR4:", result)

result = fetch_gdelt_sentiment("VALE3", "2026-06-01", window_days=3)
print("Resultado VALE3:", result)
