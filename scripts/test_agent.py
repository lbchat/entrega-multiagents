"""Teste de fumaça do agente completo."""
from quantumfinance.agents.orchestrator import ask

print("=" * 50)
print("TESTE 1: Recomendação completa")
print("=" * 50)
response = ask("Qual a recomendação para PETR4 hoje?")
print(response)

print("\n" + "=" * 50)
print("TESTE 2: Pergunta pontual — só indicadores")
print("=" * 50)
response = ask("Qual o RSI atual da PETR4?")
print(response)

print("\n" + "=" * 50)
print("TESTE 3: Pergunta pontual — só sentimento")
print("=" * 50)
response = ask("Qual o sentimento das notícias sobre PETR4?")
print(response)
