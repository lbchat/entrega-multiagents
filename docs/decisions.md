# Decisões Arquiteturais

## Arquitetura de agentes
**Decisão:** 3 agentes especializados + orquestrador (MarketAgent, SentimentAgent, DecisionAgent).
**Motivo:** mínimo funcional que atende os requisitos da disciplina. Cada agente tem responsabilidade única e clara.
**Atenção:** `create_react_agent` do LangGraph instalado (1.2.6) não aceita mais o parâmetro `state_modifier` usado em versões antigas — o nome correto é `prompt`. Aplicado nos três agentes.

## Coordenação do orquestrador
**Decisão:** padrão híbrido — pipeline fixo para recomendação completa, roteamento dinâmico para perguntas pontuais.
**Motivo:** o pipeline fixo garante confiabilidade no caso principal. O roteamento torna a interface conversacional fluida e eficiente.
**Implementação:** primeiro nó do grafo LangGraph é um nó de roteamento condicional que classifica a intenção da pergunta.

## Pipeline determinístico no fluxo de recomendação
**Decisão:** as etapas `pipeline_market`, `pipeline_sentiment` e `pipeline_decision` do orquestrador chamam as tools diretamente em Python, sem passar pelo ReAct do LLM. O LLM só entra na etapa final para narrar o resultado.
**Motivo:** confiabilidade garantida no caminho principal — elimina o risco de o modelo pular uma etapa ou chamar a tool errada.
**Trade-off aceito:** o fluxo de recomendação é menos "agêntico" no sentido puro, compensado pelo roteamento dinâmico genuíno nas perguntas pontuais (`market_node`, `sentiment_node`).

## LLM principal
**Decisão:** Qwen 2.5 7B Instruct via DeepInfra API.
**Motivo:** open source, baixa latência via API, compatível com OpenAI SDK, créditos disponíveis (~$5). Se tool calling apresentar inconsistências, fallback para Llama 3.1 8B — muda apenas `config.py`.
**Integração:** `langchain_openai.ChatOpenAI` com `base_url="https://api.deepinfra.com/v1/openai"`.

## Modelo de sentimento
**Decisão:** FinBERT-PT-BR via HuggingFace transformers, apenas inferência.
**Motivo:** modelo especializado em sentimento financeiro em português. Não treinar — usar pré-treinado.
**Atenção:** não usar LeIA/VADER em paralelo. Um único modelo de sentimento no caminho crítico.

## Persistência de estado
**Decisão:** CSV e JSON locais em `data/`.
**Motivo:** simplicidade máxima, legível por humanos, versionável, e o CSV é insumo direto do backtest.
- `data/recommendations.csv` — histórico de recomendações
- `data/sessions.json` — memória de curto prazo do Gradio

## Formato de saída da recomendação
**Decisão:** JSON estruturado internamente, convertido para texto natural na exibição.
**Motivo:** JSON garante consistência para persistência e backtest. Texto natural melhora a experiência na demo.
**Campos obrigatórios do JSON:** ticker, date, recommendation, confidence, rsi, macd_signal, sentiment_score, sentiment_label, top_headlines, reasoning.
**Enum de recomendação:** sempre validar contra `Recommendation(COMPRAR, VENDER, AGUARDAR)` antes de persistir.
**Atenção:** `model_dump()` simples retorna o membro do enum (`<Recommendation.COMPRAR: 'COMPRAR'>`) em vez da string `"COMPRAR"`, corrompendo a escrita em CSV. Sempre usar `model_dump(mode="json")` em `RecommendationOutput`.

## Backtest sem look-ahead bias
**Decisão:** o backtest (`run_backtest`) não chama o LLM nem o FinBERT — usa apenas indicadores técnicos via função pura (`apply_decision_rules`) e sentimento fixo neutro (`sentiment_score=0.5`) para todas as datas.
**Motivo:** narrativa em linguagem natural não agrega valor num loop histórico de centenas de dias; sentimento real de notícias não está disponível para datas passadas via RSS (só existe para o presente).
**Atualização (Etapa 6.5):** o sentimento fixo neutro continua sendo o comportamento com `use_gdelt=False`; por padrão (`use_gdelt=True`) o backtest agora usa sentimento histórico real via GDELT/BigQuery — ver decisão "Sentimento histórico via GDELT/BigQuery" abaixo.
**Atenção (look-ahead bias):** `end=` no `yf.download` é **exclusivo** (confirmado empiricamente, não documentado claramente pelo yfinance) — `yf.download(ticker, end=date)` retorna dados só até o pregão **anterior** a `date`, nunca incluindo `date`. Por isso `get_historical_features(ticker, date)` (`targets.py`) calcula os indicadores com o fechamento do último pregão antes de `date`, nunca o de `date` em si — uma proteção contra look-ahead bias ainda mais conservadora que o mínimo exigido (nunca usa nem o próprio dia da decisão). Já `start=` é inclusivo (confirmado também) — por isso `get_forward_return`/`get_ibovespa_return` usam `start=date`, garantindo que o retorno futuro seja medido a partir do preço real de `date`, o dia da decisão.

## Sentimento histórico via GDELT/BigQuery (Etapa 6.5)
**Decisão:** substituir completamente o cliente GDELT baseado em API REST (`gdeltdoc`) por Google BigQuery como fonte canônica de sentimento histórico no backtest. Esta é a implementação definitiva, não uma melhoria futura.
**Motivo:** a API REST do GDELT tinha rate limiting severo e não documentado oficialmente — ~30min para coletar 3 semanas de dados de 4 tickers — o que tornaria o backtest completo de 90 dias um processo de várias horas. O BigQuery acessa o mesmo dataset público do GDELT sem esse rate limit.
**Implementação:** `google-cloud-bigquery` consultando `gdelt-bq.gdeltv2.gkg_partitioned` (a mesma GKG do GDELT, particionada por dia via `_PARTITIONTIME`, o que permite poda de partição e reduz bytes escaneados de ~21TB para ~0.3-0.5GB por consulta). Filtro por `AllNames LIKE` com as keywords de `TICKER_KEYWORDS` via `UNNEST` — sem as restrições de tamanho/caracteres especiais que a API REST impunha (`_safe_gdelt_keywords` deixou de ser necessário, a lista completa de keywords é usada). Tone extraído do primeiro campo de `V2Tone` (`SPLIT(...)[OFFSET(0)]`), agregado com `AVG` no próprio BigQuery e normalizado com `(tone+10)/20`. Project ID do GCP: `entrega-multi-agents` (autenticação via Application Default Credentials do `gcloud`, sem chave de serviço no repositório).
**Trade-off aceito:** `fetch_gdelt_sentiment` ainda dispara uma query BigQuery sequencial por combinação ticker/dia — para o backtest completo (90 dias × 4 tickers = 243 chamadas) isso leva ~25min. Aceitável para o volume atual (minutos, não as horas da API REST), mas não escala indefinidamente. Melhoria futura documentada em `docs/progress.md`: uma única query em lote (`GROUP BY ticker, date`) cobrindo todo o período, e download bulk no `yfinance` (mesmo padrão de chamada sequencial em `get_historical_features`/`get_forward_return`, `targets.py`).

## Working directory do notebook de backtest — notebooks/data/ separado de data/
**Observação:** `notebooks/04_backtest_and_evaluation.ipynb` executa com o diretório de trabalho igual ao diretório do próprio notebook (`notebooks/`), não a raiz do repositório — comportamento padrão do `jupyter nbconvert --execute` e também de kernels Jupyter configurados com `notebookFileRoot` relativo ao arquivo. Por isso os caminhos relativos usados nas células (ex: `Path("data/backtest_results.csv")`) resolvem para `notebooks/data/...`, não `data/...` na raiz — daí a pasta `notebooks/data/` (e `notebooks/reports/figures/`) existir separada da `data/` usada pelos `scripts/` (que são executados a partir da raiz do repo, ex: `scripts/run_backtest_gdelt.py` escreve em `<raiz>/data/backtest_results_gdelt.csv`).
**Atenção:** os dois diretórios não são o mesmo — um `pd.read_csv("data/algo.csv")` dentro do notebook nunca encontra um arquivo salvo em `<raiz>/data/`. Para comparar um resultado gerado por um script (raiz) com o que o notebook espera ler, é preciso copiar o CSV para `notebooks/data/` antes de rodar a célula de leitura. Isso explica por que `data/backtest_results_gdelt.csv` (raiz, gerado por `scripts/run_backtest_gdelt.py`) e `notebooks/data/backtest_results_gdelt.csv` (cópia, lida pela célula de comparação) coexistem no repositório.

## Biblioteca de indicadores técnicos
**Decisão:** pandas-ta.
**Motivo:** TA-Lib tem dependência nativa que causa problemas de instalação em Windows. pandas-ta é pure Python.

## Testes
**Decisão:** pytest focado em ~15 funções críticas.
**O que testar:** cálculo de RSI (valor entre 0-100), MACD (3 componentes), sentimento (formato correto), parser de notícias (feed vazio sem crash), validação do enum de recomendação, campos obrigatórios no JSON de saída.

## Ticker do MVP
**Decisão:** PETR4.
**Motivo:** alta liquidez, volume alto de notícias em português, toca múltiplas esferas contextuais (energia, política, geopolítica).

## O que não está no caminho crítico
- Azure, redes sociais — extensões de portfólio, não dependências do MVP
- Context Router e análise por esferas — bônus, implementar após Etapa 5
- Modelo supervisionado sobre features históricas — bônus, implementar após Etapa 6
- Deep Learning (LSTM, Transformer) — deixar para projeto futuro
