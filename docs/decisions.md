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
- Azure, GDELT, redes sociais — extensões de portfólio, não dependências do MVP
- Context Router e análise por esferas — bônus, implementar após Etapa 5
- Modelo supervisionado sobre features históricas — bônus, implementar após Etapa 6
- Deep Learning (LSTM, Transformer) — deixar para projeto futuro
