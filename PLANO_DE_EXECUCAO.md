# Plano de Execução — QuantumFinance AI Agent

---

## Parte 1 — Plano de Execução por Etapas

### Etapa 0 — Fundação do projeto

Antes de escrever qualquer linha de código do agente, deixe a base pronta. Isso parece óbvio mas é onde a maioria dos projetos acadêmicos começa torto.

- Criar o repositório no GitHub (público, com README inicial mesmo que mínimo)
- Configurar ambiente Python com `pyproject.toml` ou `requirements.txt` enxuto — só o que você sabe que vai usar
- Criar `.env.example` com as variáveis necessárias: `DEEPINFRA_API_KEY`
- Definir a estrutura de pastas mínima, sem criar pastas vazias "para o futuro"
- Colocar `CLAUDE.md` na raiz e a pasta `docs/` com os quatro arquivos de contexto
- **Validar o LLM antes de qualquer código de agente:** fazer uma chamada simples ao Qwen 2.5 7B via DeepInfra, com uma pergunta que exige tool calling, e confirmar que o formato de resposta é compatível com LangGraph. Se houver inconsistência, trocar para Llama 3.1 8B — muda apenas uma linha em `config.py`.

**Critério de saída:** `python -c "import quantumfinance"` funciona, o repo está no GitHub, o README explica em 3 parágrafos o que o projeto faz, e uma chamada de teste ao Qwen 2.5 7B via DeepInfra retornou uma tool call bem formatada.

---

### Etapa 1 — Pipeline de dados de mercado

O objetivo é ter uma função que recebe um ticker e retorna preços + indicadores técnicos prontos para uso. Sem agente ainda, sem LLM, sem nada de IA.

- Implementar coleta via `yfinance` para um ticker, retornando OHLCV
- Calcular os indicadores que a disciplina pede: RSI, MACD, SMA, EMA, Bandas de Bollinger, Volume
- Usar `pandas-ta` — nunca TA-Lib (dependência nativa problemática em Windows)
- Validar visualmente em notebook: plotar preço + indicadores e conferir se faz sentido

**Critério de saída:** uma função `get_market_features("PETR4")` que devolve um dicionário com preço atual e indicadores calculados, e um notebook com os gráficos validados.

---

### Etapa 2 — Pipeline de notícias e sentimento

Coleta de notícias e classificação de sentimento com FinBERT-PT-BR.

- Coleta via `feedparser` de RSS feeds (InfoMoney, Valor Econômico, Reuters, B3)
- Filtro por keywords ligadas ao ticker (Petrobras, PETR4, petróleo, combustíveis…)
- Carregamento do modelo FinBERT-PT-BR via HuggingFace `transformers` — apenas inferência, sem fine-tuning
- Classificação de sentimento de cada notícia (POSITIVO / NEGATIVO / NEUTRO + score de confiança)
- Agregação: score médio de sentimento e contagem das últimas N notícias

**Critério de saída:** uma função `get_sentiment_features("PETR4")` que devolve um dicionário com sentimento médio recente, número de notícias analisadas, e as 3 manchetes mais relevantes com seus scores.

---

### Etapa 3 — Construção do agente MVP

Com as funções das etapas 1 e 2 funcionando, transformá-las em tools e montar o agente é direto.

- Criar 3 tools: `get_market_features`, `get_sentiment_features`, `generate_recommendation`
- Implementar o grafo LangGraph com os 3 agentes especializados + orquestrador
- Orquestrador com padrão híbrido: pipeline fixo (Market → Sentiment → Decision) para recomendação completa, roteamento dinâmico para perguntas pontuais
- Definir o prompt de sistema de cada agente com responsabilidade única e explícita
- Implementar memória de sessão básica para conversas multi-turno
- Garantir que o raciocínio (Chain-of-Thought) seja registrado de forma estruturada
- Saída do DecisionAgent: JSON estruturado validado contra o enum `Recommendation(COMPRAR, VENDER, AGUARDAR)`

**Critério de saída:** você pergunta no terminal "qual a recomendação para PETR4 hoje?" e o agente responde com COMPRAR/VENDER/AGUARDAR + justificativa baseada em dados reais coletados naquele momento.

---

### Etapa 4 — Expansão para os 4 tickers

Com o agente funcionando para PETR4, generalizar é simples. O cuidado é não introduzir bugs na expansão.

- Parametrizar todas as funções para qualquer ticker
- Testar caso a caso — VALE3 tem dinâmica diferente de BBAS3, e isso pode revelar bugs
- Garantir que `TICKERS = ["PETR4", "VALE3", "BBAS3", "ITUB4"]` em `config.py` seja a única fonte de verdade
- Validar que o agente lida bem com perguntas comparativas ("compare VALE3 e PETR4 hoje")

**Critério de saída:** o agente responde corretamente para os 4 tickers e mantém qualidade nas justificativas em todos eles.

---

### Etapa 5 — Interface conversacional (Gradio)

Coloque uma cara no projeto. Gradio transforma o agente em algo demonstrável e gravável.

- Interface mínima: campo de pergunta + área de resposta + histórico de conversa
- Mostrar o raciocínio do agente em seção colapsável (transparência do CoT)
- Botões de exemplo pré-definidos: "Recomendação para PETR4", "Compare VALE3 e BBAS3", "Qual o sentimento atual de ITUB4?"

**Critério de saída:** demo navegável no browser, gravável em vídeo curto para portfólio.

---

### Etapa 6 — Backtest e registro de recomendações

Aqui o projeto passa de "agente funcional" para "agente avaliável". É o que mais impressiona na avaliação acadêmica e em portfólio.

- Implementar simulação histórica: rodar o agente com dados de cada dia útil dos últimos 6-12 meses
- Para cada dia, registrar em `data/recommendations.csv`: data, ticker, recomendação, confiança, indicadores, sentimento, raciocínio
- Comparar performance vs. buy-and-hold e vs. Ibovespa
- Calcular métricas: acurácia direcional, retorno acumulado, Sharpe ratio simplificado

**Critério de saída:** notebook de backtest com gráficos comparativos e tabela de métricas.

---

### Etapa 7 — Documentação final e entrega

A documentação é onde projetos bons viram excelentes para portfólio.

- README completo: o problema, a solução, arquitetura, como rodar, limitações, próximos passos
- Notebook de demonstração que orquestra tudo do início ao fim
- Vídeo curto (2-3 min) mostrando o agente funcionando
- Diagrama da arquitetura em Mermaid ou Excalidraw
- Lista honesta de limitações — mostra maturidade técnica

**Critério de saída:** alguém que abre o repo entende o projeto em 5 minutos e consegue rodar localmente em 15.

---

## Parte 2 — Banco de Ideias Bônus

Implementar apenas após a Etapa 5 concluída, em ordem de prioridade para portfólio.

### 🥇 1. Asset Context Map + Context Router Agent

**O que é:** sistema de mapeamento contextual por ativo com esferas temáticas (política, ambiental, social, regulatória) e um agente roteador que dirige buscas de notícia para as fontes e keywords certas por esfera.

**Quando incorporar:** após Etapa 5, antes do backtest. Implementar para PETR4 primeiro.

**Por que vale para portfólio:** é a ideia mais original do planejamento. Quase ninguém vai pensar nisso. Em entrevista técnica vira história: *"percebi que sentimento genérico perdia o contexto setorial, então construí um sistema de roteamento contextual..."*. Mostra pensamento de produto e arquitetura, não só execução.

---

### 🥈 2. Backtest comparativo robusto

**O que é:** aprofundamento do backtest da Etapa 6 com walk-forward validation, análise por regime de mercado (bull vs. bear) e drawdown máximo.

**Quando incorporar:** após Etapa 6, como extensão natural.

**Por que vale para portfólio:** rigor quantitativo é raro em projetos de agentes. A maioria para no "o agente funciona". Quem valida com seriedade se destaca.

---

### 🥉 3. Análise por esferas contextuais

**O que é:** camada de sentimento contextual além do financeiro direto — política, ambiental, social, regulatória. Implementação natural após o Context Router existir.

**Quando incorporar:** logo após o Asset Context Map. Começar com 2 esferas por ticker, não 9.

**Por que vale para portfólio:** completa a tese intelectual do projeto e gera material rico para discussão em entrevista — envolve trade-offs claros de precisão vs. cobertura e ruído vs. sinal.

---

### 4. Memória de longo prazo do agente

**O que é:** o agente lembra recomendações anteriores e eventos passados relevantes, injetando esse contexto em chamadas futuras via arquivo JSON ou SQLite.

**Quando incorporar:** após Etapa 4.

**Por que vale para portfólio:** memória é um dos tópicos mais discutidos em sistemas de agentes hoje. Mostra entendimento do ciclo de vida de um agente em produção.

---

### 5. Modelo supervisionado sobre recomendações históricas

**O que é:** após o backtest gerar centenas de recomendações com features e resultados reais, treinar um modelo simples (Random Forest ou Logistic Regression) para aprender quais combinações de features predizem boas recomendações.

**Quando incorporar:** após Etapa 6, como camada de calibração do DecisionAgent.

**Por que vale para portfólio:** demonstra integração entre agentes e ML clássico — combinação rara e valorizada. Fecha o loop intelectual do planejamento original de forma sólida.

---

### 6. Alertas automáticos (Telegram)

**O que é:** o agente roda diariamente via GitHub Actions e envia recomendações por mensagem no Telegram.

**Quando incorporar:** após a entrega acadêmica, como extensão de portfólio.

**Por que vale para portfólio:** transforma o projeto acadêmico em produto real e demonstrável. *"Ele me manda mensagens todo dia"* é uma frase poderosa em entrevista.

---

### 7. Persistência em nuvem (Azure Blob Storage)

**O que é:** salvar CSVs de recomendações, gráficos e logs no Azure usando os créditos disponíveis.

**Quando incorporar:** após Etapa 6.

**Por que vale para portfólio:** adiciona Azure ao escopo do projeto, útil em filtros de RH. Implementação simples com retorno visível no repositório.

---

### 8. Comparador de carteiras por perfil de risco

**O que é:** o agente recebe um perfil (conservador, moderado, agressivo) e monta uma sugestão de alocação entre os 4 tickers.

**Quando incorporar:** apenas se sobrar tempo após todas as etapas anteriores.

**Por que vale para portfólio:** mostra visão de produto e UX. Mais relevante para papéis de aplicação de IA do que pesquisa.

---

### 9. Deep Learning experimental (LSTM / Transformer temporal)

**O que é:** modelo de série temporal para prever direção do preço.

**Quando incorporar:** deixar para um projeto futuro, fora do escopo desta entrega.

**Por que está listado mesmo assim:** estava no planejamento original. A recomendação concreta é não incluir — com 4 ativos, o risco de overfitting é alto e a explicabilidade cai, o que penaliza na avaliação acadêmica.
