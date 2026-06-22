# QuantumFinance AI Agent

Sistema multiagente de recomendação de ações brasileiras (COMPRAR / VENDER / AGUARDAR) combinando indicadores técnicos e análise de sentimento de notícias, com justificativa auditável.

## Stack
- Python 3.11+, LangGraph, DeepInfra API (Qwen/Qwen3-235B-A22B-Instruct-2507)
- FinBERT-PT-BR — sentimento financeiro em português
- yfinance + feedparser — dados de mercado e notícias RSS
- pandas-ta — indicadores técnicos (nunca TA-Lib)
- Gradio — interface conversacional
- pytest + ruff + mypy — testes, lint e tipos

## Ambiente
- Windows 11, PowerShell — usar comandos PowerShell, não bash

## Estrutura
- `src/quantumfinance/data/` — coleta de preços e notícias
- `src/quantumfinance/features/` — indicadores técnicos e sentimento
- `src/quantumfinance/agents/` — orquestrador e agentes especializados
- `src/quantumfinance/tools/` — tools registradas nos agentes
- `src/quantumfinance/output/` — formatação e persistência
- `src/quantumfinance/app/` — Gradio
- `tests/` — pytest focado em funções críticas
- `data/` — recommendations.csv e sessions.json (gerados em runtime)

## Comandos
- Interface: `python src/quantumfinance/app/gradio_app.py`
- Testes: `pytest tests/ -v`
- Lint: `ruff check src/`
- Tipos: `mypy src/`

## Verificação após cada mudança
1. `mypy src/` — corrigir erros de tipo
2. `pytest tests/ -v` — corrigir testes quebrados
3. `ruff check src/` — corrigir lint

## Não faça
- Nunca use TA-Lib — use pandas-ta
- Nunca hardcode tickers — use `TICKERS` de `config.py`
- Nunca hardcode API keys — use `.env` via python-dotenv
- Nunca coloque lógica de negócio nos agentes — fica nas tools e em `features/`
- Nunca embaralhe dados no backtest — sempre ordem temporal
- Nunca use model_dump() simples em RecommendationOutput — sempre model_dump(mode="json") para garantir serialização correta do enum Recommendation.

## Referências
- Arquitetura e decisões: `docs/decisions.md`
- Padrões de código e exemplos de tools: `docs/patterns.md`
- Estado atual e próximas etapas: `docs/progress.md`
- Estilo de código: `docs/code-style.md`
