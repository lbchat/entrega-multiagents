# QuantumFinance AI Agent

Sistema multiagente que recomenda **COMPRAR / VENDER / AGUARDAR** para ações brasileiras, combinando indicadores técnicos com análise de sentimento de notícias — com justificativa auditável em linguagem natural, não uma caixa-preta.

## O problema e a solução

Decidir comprar, vender ou esperar uma ação exige cruzar dois tipos de informação que normalmente vivem em lugares separados: **o que os números dizem** (preço, RSI, MACD, médias móveis) e **o que está sendo noticiado** sobre a empresa (resultado trimestral, troca de diretoria, risco regulatório). Fazer isso manualmente, todos os dias, para várias ações, não escala.

A solução aqui é um **agente multiagente**: um orquestrador que decide se a pergunta do usuário pede uma recomendação completa ou só um dado pontual, e direciona o trabalho para agentes especializados — um que só olha mercado, um que só olha sentimento, e um que combina os dois numa recomendação final com a lógica explicada. Cada recomendação fica registrada em CSV com todos os indicadores que a motivaram, então é possível voltar e auditar por que o agente decidiu o que decidiu.

O sistema cobre 4 ações da B3: **PETR4 · VALE3 · BBAS3 · ITUB4**.

## Arquitetura

3 agentes especializados (`MarketAgent`, `SentimentAgent`, `DecisionAgent`) + um orquestrador em LangGraph com coordenação **híbrida**:

- **Pipeline fixo** (`pipeline_market → pipeline_sentiment → pipeline_decision`) para recomendação completa — as tools são chamadas diretamente em Python, sem passar pelo LLM, garantindo que a etapa nunca seja pulada ou a tool errada seja chamada. O LLM (`DecisionAgent`) só entra no fim para narrar o resultado já calculado.
- **Roteamento dinâmico** (`market_node`, `sentiment_node`) para perguntas pontuais ("qual o RSI de VALE3?") — aqui o LLM decide de fato quais tools chamar, ReAct genuíno.

Diagrama completo (fluxo do agente + pipeline do backtest) em [`docs/architecture.md`](docs/architecture.md). Decisões e trade-offs detalhados em [`docs/decisions.md`](docs/decisions.md).

## Como rodar localmente

### Pré-requisitos
- Python 3.11+
- Conta na [DeepInfra](https://deepinfra.com/) com chave de API (créditos gratuitos cobrem a demo)
- *(Opcional — só para reproduzir o backtest com sentimento histórico real)* conta Google Cloud com BigQuery habilitado e `gcloud` CLI autenticado

### Instalação

```powershell
git clone <url-do-repositorio>
cd ENTREGA_MULTI-AGENTS
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### Configuração

```powershell
Copy-Item .env.example .env
# edite .env e preencha DEEPINFRA_API_KEY
```

Para reproduzir o backtest com sentimento histórico real (opcional, não necessário para a interface principal):

```powershell
gcloud auth application-default login
```

### Rodar a interface conversacional

```powershell
python src/quantumfinance/app/gradio_app.py
```

Abre em `http://localhost:7860`. Exemplos de pergunta: "Qual a recomendação para PETR4 hoje?", "Compare os indicadores de VALE3 e PETR4", "Qual o sentimento das notícias sobre BBAS3?".

### Rodar os testes e checagens de qualidade

```powershell
pytest tests/ -v       # 20 testes, funções críticas
mypy src/               # tipos
ruff check src/         # lint
```

### Reproduzir o backtest (opcional)

```powershell
python scripts/run_backtest_gdelt.py
```

## Resultados do backtest

Simulação histórica nos últimos ~90 dias úteis, para os 4 tickers, comparando a recomendação do dia contra o retorno real dos 5 pregões seguintes e contra o Ibovespa no mesmo período. O backtest **não chama o LLM nem o FinBERT** — usa só a função determinística de decisão (`apply_decision_rules`), para isolar a qualidade do sinal técnico+sentimento da qualidade da narração em linguagem natural.

| Modo | Linhas | Accuracy direcional | Beat Ibovespa | Sentimento |
|---|---|---|---|---|
| Placeholder (sentimento neutro fixo) | 229 | ~40% | ~52% | `sentiment_score=0.5` sempre |
| GDELT/BigQuery (sentimento histórico real) | 243 | ~42% | ~53.8% | 100% real, 0% fallback |

*(Os valores exatos variam um pouco entre execuções porque a janela do backtest é sempre "os últimos 90 dias" — rolante, não fixa. Os números acima são representativos do que o notebook `04_backtest_and_evaluation.ipynb` produz.)*

**Leitura honesta dos números:** accuracy de ~40-42% numa decisão de 3 classes (COMPRAR/VENDER/AGUARDAR, baseline aleatório ~33%) é acima do acaso, mas não é um sinal validado para uso real — é evidência de que a lógica é sã, não de que é lucrativa. Bater o Ibovespa em ~52-54% das vezes também está perto de um cara-ou-coroa. O ganho mais sólido do sentimento real (GDELT) sobre o placeholder neutro foi pequeno e concentrado em poucos dias específicos (ver notebook), porque a maior parte do tempo o sentimento de notícias fica numa faixa neutra que não muda a decisão (`apply_decision_rules` só deixa o sentimento influenciar quando o score passa de 0.6 ou cai abaixo de 0.4).

Detalhes completos, gráficos e a comparação lado a lado dos dois modos: [`notebooks/04_backtest_and_evaluation.ipynb`](notebooks/04_backtest_and_evaluation.ipynb).

## Decisões arquiteturais principais

- **Pipeline determinístico no fluxo de recomendação** — encadear 3 agentes ReAct passando a conversa acumulada não funcionava de forma confiável (o LLM via a conversa "já parecendo respondida" e não chamava a tool). A solução foi chamar as tools direto em Python no caminho principal, com o LLM entrando só para narrar.
- **Sentimento histórico via Google BigQuery** — o cliente GDELT original via API REST tinha rate limiting severo (~30min para 3 semanas de dados). Substituído por BigQuery, que acessa o mesmo dataset público do GDELT sem esse limite, terminando o backtest completo em minutos em vez de horas.
- **FinBERT-PT-BR para sentimento** — modelo especializado em sentimento financeiro em português, usado só para inferência (sem fine-tuning), no caminho em tempo real do agente.

Rationale completo de cada decisão, incluindo os trade-offs aceitos: [`docs/decisions.md`](docs/decisions.md).

## Limitações honestas

- **Sentimento em tempo real depende de RSS, que é volátil por natureza.** A cobertura de notícias para um ticker específico, num dado momento, depende do que os feeds têm publicado nas últimas horas — pode não ter nada relevante, e o sistema cai no fallback neutro (`sentiment_score=0.5`) sem aviso explícito ao usuário.
- **Sentimento histórico do backtest (GDELT) é um score geral de mídia, não financeiro especializado** — diferente do FinBERT-PT-BR usado no agente em tempo real. É uma proxy razoável para o backtest, não o mesmo sinal usado em produção.
- **Latência sequencial no backtest com BigQuery** — uma query por combinação ticker/dia (243 chamadas para 90 dias × 4 tickers, ~25min). Funciona bem no volume atual, mas não é a forma mais eficiente; batch queries reduziriam isso a poucas chamadas (ver Próximos passos).
- **Matching de keywords é por substring exato, não semântico** — uma manchete pode "casar" com um ticker por uma palavra genérica (ex: "juros", "Selic") sem ser realmente sobre aquela empresa. A manchete completa fica visível para auditoria, mas o filtro em si não distingue relevância genuína de coincidência de termo.
- **Pipeline fixo é menos "agêntico" no sentido puro** — o caminho principal de recomendação não deixa o LLM decidir a sequência de tools; isso é uma troca deliberada por confiabilidade, não uma limitação técnica não-percebida (ver decisão acima).
- **Accuracy do backtest é uma prova de conceito, não um sinal validado** — ver "Resultados do backtest" acima.
- **Dependência de serviços externos** — DeepInfra (LLM), Yahoo Finance, feeds RSS e BigQuery precisam estar disponíveis; o sistema tem fallbacks (sentimento neutro, mensagens de erro amigáveis no Gradio) mas não funciona totalmente offline.

## Próximos passos

- **Batch queries no BigQuery e download bulk no yfinance** — substituir as centenas de chamadas sequenciais do backtest por uma única query agregada (`GROUP BY ticker, date`) e um único `yf.download` por ticker, eliminando a maior parte dos round-trips de rede.
- **Integração com dados da CVM** — fundamentos e divulgações regulatórias das empresas monitoradas, complementando o sentimento de notícias com dados estruturados oficiais.
- **Integração com o Boletim Focus do Banco Central** — expectativas de mercado para Selic, inflação e câmbio como contexto macroeconômico adicional na decisão.
- **Context Router Agent** — agente que decide dinamicamente quais esferas temáticas (política, ambiental, regulatória) são relevantes para cada ticker antes de buscar sentimento, em vez do conjunto fixo de keywords atual.

## Stack

Python 3.11+ · LangGraph · DeepInfra (Qwen3-235B-A22B-Instruct) · FinBERT-PT-BR · yfinance · feedparser · pandas-ta · Google BigQuery · Gradio · pytest/ruff/mypy

## Estrutura do projeto

```
src/quantumfinance/
├── data/          # coleta de preços, notícias e sentimento histórico (GDELT/BigQuery)
├── features/      # indicadores técnicos, sentimento, targets do backtest
├── agents/        # MarketAgent, SentimentAgent, DecisionAgent, orquestrador
├── tools/         # tools registradas nos agentes
├── output/        # persistência das recomendações
├── backtesting/   # simulação histórica e métricas
└── app/           # interface Gradio
tests/             # pytest das funções críticas
notebooks/         # validação visual e demo end-to-end
docs/              # decisões, progresso, padrões de código, arquitetura
```
