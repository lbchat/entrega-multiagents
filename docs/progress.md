# Estado do Projeto

> Atualizar esta seção ao concluir cada etapa.

## Etapas

- [x] **Etapa 0** — Fundação: repositório, ambiente, estrutura de pastas, .env.example, README inicial
- [x] **Etapa 1** — Pipeline de mercado: yfinance + pandas-ta funcionando para PETR4, validado em notebook
- [x] **Etapa 2** — Pipeline de sentimento: feedparser + FinBERT-PT-BR funcionando para PETR4, validado em notebook
- [ ] **Etapa 3** — Agente MVP: 3 tools + ReAct + recomendação completa para PETR4
- [ ] **Etapa 4** — Expansão: agente funcionando para VALE3, BBAS3 e ITUB4
- [ ] **Etapa 5** — Interface Gradio: demo conversacional navegável
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

## Notas e blockers

<!-- Registre aqui impedimentos, dúvidas abertas ou decisões tomadas durante a implementação -->

- O AVG Antivirus faz inspeção HTTPS (MITM) e bloqueia chamadas SSL do Python com `CERTIFICATE_VERIFY_FAILED`. Corrigido instalando `pip-system-certs` no `.venv` (faz o Python confiar no certificado store do Windows). Se reinstalar o venv do zero, repetir esse passo.
- `yfinance` usa `curl_cffi` por baixo dos panos, que tem seu próprio bundle de certificados e não é coberto pelo `pip-system-certs`. Corrigido exportando o certificado raiz do AVG (`Cert:\LocalMachine\Root`, assunto "AVG Web/Mail Shield Root") e anexando ao `cacert.pem` do `certifi` dentro do `.venv`. Se reinstalar o venv do zero, repetir esse passo também.
- O `id2label` real do `lucas-leme/FinBERT-PT-BR` é `{0: POSITIVE, 1: NEGATIVE, 2: NEUTRAL}`, não `{0: negativo, 1: neutro, 2: positivo}` como assumido inicialmente em `sentiment.py`. Corrigido a ordem da lista `labels`. Há um teste de regressão (`test_classify_sentiment_correct_polarity`) que pegaria esse bug se reaparecer.
