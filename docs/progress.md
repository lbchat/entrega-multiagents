# Estado do Projeto

> Atualizar esta seção ao concluir cada etapa.

## Etapas

- [x] **Etapa 0** — Fundação: repositório, ambiente, estrutura de pastas, .env.example, README inicial
- [x] **Etapa 1** — Pipeline de mercado: yfinance + pandas-ta funcionando para PETR4, validado em notebook
- [x] **Etapa 2** — Pipeline de sentimento: feedparser + FinBERT-PT-BR funcionando para PETR4, validado em notebook
- [x] **Etapa 3** — Agente MVP: 3 tools + ReAct + recomendação completa para PETR4
- [x] **Etapa 4** — Expansão: agente funcionando para VALE3, BBAS3 e ITUB4
- [x] **Etapa 5** — Interface Gradio: demo conversacional navegável
- [ ] **Etapa 6** — Backtest: simulação histórica + comparação vs. buy-and-hold e Ibovespa
- [ ] **Etapa 7** — Entrega: README final, diagrama de arquitetura, documentação de limitações

## Bônus (implementar após Etapa 5, em ordem de prioridade)

- [ ] Asset Context Map + Context Router Agent
- [ ] Backtest aprofundado (walk-forward, métricas financeiras completas)
- [ ] Análise por esferas contextuais (política, ambiental, social)
- [ ] Memória de longo prazo do agente
- [ ] Modelo supervisionado sobre features históricas
- [ ] Alertas automáticos via Telegram
- [ ] Persistência em Azure Blob Storage

### Ideias para destacar agência real (ReAct) no portfólio

**Sugestão 1 — Agente de perguntas livres (já implementado, precisa ser destacado)**

O roteamento dinâmico para perguntas pontuais (`market_node`, `sentiment_node`) já é ReAct genuíno — o LLM decide quais tools chamar e em que ordem sem sequência pré-determinada. Não requer código novo: apenas criar exemplos demonstráveis no notebook e no Gradio que tornem esse comportamento visível e explícito para o avaliador.

**Sugestão 2 — Agente de diagnóstico investigativo**

Novo modo de pergunta aberta onde o usuário pode perguntar coisas como "Por que VALE3 está caindo?" ou "O que explica o comportamento de PETR4 hoje?". Esse tipo de pergunta não tem resposta determinística — o agente precisa decidir autonomamente quais tools consultar, em que ordem, e quando tem informação suficiente para responder. É ReAct no sentido mais puro e demonstrável, com Chain-of-Thought visível no Gradio. Implementação: um quarto nó no orquestrador ativado para perguntas abertas que não se encaixam nos três roteamentos existentes.

**Sugestão 4 — Context Router Agent (bônus de maior valor para portfólio)**

Agente que recebe um ticker e decide autonomamente quais dimensões contextuais analisar (política, ambiental, regulatória, macroeconômica) antes de buscar sentimento. A decisão de quais esferas são relevantes para VALE3 vs. PETR4 é genuinamente dinâmica e não pode ser determinística — é ReAct por natureza. Requer o Asset Context Map (`context_map.yaml`) com keywords por esfera por ticker. É o argumento mais forte para demonstrar agência real do sistema, e o item de maior diferenciação para portfólio.

## Notas e blockers

<!-- Registre aqui impedimentos, dúvidas abertas ou decisões tomadas durante a implementação -->

- O AVG Antivirus faz inspeção HTTPS (MITM) e bloqueia chamadas SSL do Python com `CERTIFICATE_VERIFY_FAILED`. Corrigido instalando `pip-system-certs` no `.venv` (faz o Python confiar no certificado store do Windows). Se reinstalar o venv do zero, repetir esse passo.
- `yfinance` usa `curl_cffi` por baixo dos panos, que tem seu próprio bundle de certificados e não é coberto pelo `pip-system-certs`. Corrigido exportando o certificado raiz do AVG (`Cert:\LocalMachine\Root`, assunto "AVG Web/Mail Shield Root") e anexando ao `cacert.pem` do `certifi` dentro do `.venv`. Se reinstalar o venv do zero, repetir esse passo também.
- O `id2label` real do `lucas-leme/FinBERT-PT-BR` é `{0: POSITIVE, 1: NEGATIVE, 2: NEUTRAL}`, não `{0: negativo, 1: neutro, 2: positivo}` como assumido inicialmente em `sentiment.py`. Corrigido a ordem da lista `labels`. Há um teste de regressão (`test_classify_sentiment_correct_polarity`) que pegaria esse bug se reaparecer.
- `RecommendationOutput.model_dump()` simples retorna o membro do enum (`<Recommendation.COMPRAR: 'COMPRAR'>`) em vez da string `"COMPRAR"`, o que corromperia a escrita em CSV. Usar sempre `model_dump(mode="json")` em `decision_tools.py`. Teste de regressão: `test_recommendation_output_serializes_enum_as_plain_string`.
- `create_react_agent` do LangGraph instalado (1.2.6) não aceita mais o parâmetro `state_modifier` (usado nos exemplos antigos) — o nome correto agora é `prompt`. Afeta `market_agent.py`, `sentiment_agent.py`, `decision_agent.py`.
- Import circular entre `agents/decision_agent.py` (precisa de `generate_recommendation`) e `tools/decision_tools.py` (precisa de `Recommendation`/`RecommendationOutput`). Resolvido com import tardio (dentro de `build_decision_agent()`).
- O pipeline fixo de recomendação (`pipeline_market` → `pipeline_sentiment` → `pipeline_decision`) não pode encadear 3 agentes ReAct passando a conversa acumulada — o LLM de cada etapa, vendo a conversa já "parecendo respondida" pela etapa anterior, frequentemente decide não chamar sua tool (ou recusa, ou retorna vazio), e o `DecisionAgent` chegava a alucinar uma recomendação em texto livre sem nunca chamar `generate_recommendation`, fazendo o CSV nunca ser escrito. Resolvido chamando as tools diretamente em Python nessas 3 etapas (determinístico), com um `PipelineState` carregando `ticker`/`market_features`/`sentiment_features` entre elas; o LLM (`DecisionAgent`) só entra no final para narrar o resultado já calculado. Os nós de roteamento dinâmico (`market_node`, `sentiment_node`) continuam usando os agentes ReAct normalmente — funcionam bem porque recebem só a pergunta original, sem histórico acumulado de outras etapas.
- `pandas-ta` 0.4.71b0 (versão instalada) gera nomes de coluna das Bandas de Bollinger com sufixo duplicado: `BBU_20_2.0_2.0`/`BBL_20_2.0_2.0`, não `BBU_20_2.0`/`BBL_20_2.0` como em versões mais antigas. Corrigido em `technical.py`.
- Caracteres Unicode `✓`/`✗` em `print()` quebram o console do PowerShell (codepage cp1252, não UTF-8) com `UnicodeEncodeError`, interrompendo o script no meio da execução. Substituídos por `OK:`/`FALHOU:` em ASCII em `scripts/test_expansion.py`.
- `gr.Chatbot` na versão instalada do Gradio (6.19.0) não aceita mais o parâmetro `type="messages"` (agora é o único formato, sem opção). Removido do construtor. O valor das mensagens continua sendo `{"role": ..., "content": ...}`.
- Para validar a interface Gradio com Playwright (browser real), o downloader de browsers do Playwright usa Node.js internamente e bate no mesmo problema de SSL do AVG, mas por um mecanismo diferente do Python (`certifi`) e do `yfinance` (`curl_cffi`). Corrigido setando `NODE_OPTIONS=--use-system-ca` antes de rodar `playwright install chromium`, o que faz o Node confiar no certificado store do Windows.

## Pendências antes da Etapa 6

- O feed RSS `https://valor.globo.com/rss/home/` (em `RSS_FEEDS`, `news_data.py`) retorna 0 itens (`feedparser` não lança erro, só volta vazio). Os outros dois feeds (InfoMoney, Money Times) funcionam normalmente. Isso reduz a base de notícias disponível para sentimento — investigar antes do backtest da Etapa 6, já que mais histórico de notícias pode impactar a qualidade do sinal de sentimento.
- `fetch_news` casa as keywords contra título+resumo combinados (`TICKER_KEYWORDS`, `news_data.py`), mas `top_headlines` só exibe o título — então a manchete mostrada ao usuário às vezes parece não relacionada ao ticker, quando na verdade o termo que deu o match estava no resumo. Melhoria sugerida: exibir também o trecho do resumo que gerou o match junto com o título, para tornar o motivo do match auditável.
