# Arquitetura

Duas partes independentes: o **agente em tempo real** (orquestrador LangGraph, atrás da interface Gradio) e o **backtest histórico** (script Python puro, sem LLM). Eles compartilham os mesmos indicadores técnicos e a mesma lógica de decisão (`apply_decision_rules`), mas rodam separadamente — o backtest nunca chama o agente, e o agente nunca chama o backtest.

## Agente em tempo real

O orquestrador roteia cada pergunta entre 3 destinos, dependendo da intenção classificada pelo LLM. Recomendação completa segue um **pipeline fixo** (tools chamadas direto em Python, sem o LLM decidir se/quando chamá-las); perguntas pontuais usam **ReAct genuíno** (o LLM decide quais tools chamar).

```mermaid
flowchart TD
    U([Usuário]) -->|pergunta| ROUTE{route_intent<br/>LLM classifica a intenção}

    ROUTE -->|"pergunta só sobre indicadores"| MNODE[market_node<br/>MarketAgent · ReAct]
    ROUTE -->|"pergunta só sobre sentimento"| SNODE[sentiment_node<br/>SentimentAgent · ReAct]
    ROUTE -->|"recomendação completa (padrão)"| PM[pipeline_market]

    MNODE --> RESP1([Resposta])
    SNODE --> RESP2([Resposta])

    PM -->|"chama tool direto em Python,<br/>sem o LLM decidir"| PS[pipeline_sentiment]
    PS -->|"chama tool direto em Python,<br/>sem o LLM decidir"| PD[pipeline_decision]
    PD -->|"DecisionAgent narra em<br/>linguagem natural o resultado<br/>já calculado"| RESP3([Resposta])
    PD --> CSV[(data/recommendations.csv)]

    MNODE -.usa.-> T1[[get_market_features]]
    PM -.usa.-> T1
    SNODE -.usa.-> T2[[get_sentiment_features]]
    PS -.usa.-> T2
    PD -.usa.-> T3[[generate_recommendation]]

    T1 --> D1[(yfinance + pandas-ta<br/>RSI, MACD, médias, Bollinger)]
    T2 --> D2[(feedparser RSS + FinBERT-PT-BR<br/>sentimento em português)]
    T3 --> D3[apply_decision_rules<br/>RSI + MACD + sentimento → COMPRAR/VENDER/AGUARDAR]
```

**Por que híbrido:** o pipeline fixo garante que a recomendação completa nunca falhe por o LLM "esquecer" de chamar uma tool ou alucinar um resultado sem dados reais — isso já aconteceu durante o desenvolvimento (ver `docs/progress.md`) quando as 3 etapas eram encadeadas como agentes ReAct passando a conversa acumulada. O roteamento dinâmico para perguntas pontuais não tem esse risco (recebe só a pergunta original, sem histórico acumulado), então pode usar ReAct de verdade.

## Backtest histórico

Roda fora do orquestrador, sem LLM e sem FinBERT — usa só a função pura de decisão, percorrendo cada dia útil do período em ordem temporal (nunca embaralhada, para não introduzir look-ahead bias).

```mermaid
flowchart LR
    RUN[run_backtest] --> GHF[get_historical_features<br/>yfinance, fechamento do pregão<br/>anterior à data — nunca o do próprio dia]
    RUN --> SENT{use_gdelt?}
    SENT -->|True, padrão| FGS[fetch_gdelt_sentiment<br/>BigQuery: gdelt-bq.gdeltv2.gkg_partitioned]
    SENT -->|False| NEUTRO[sentiment_score = 0.5 fixo]

    GHF --> ADR[apply_decision_rules]
    FGS --> ADR
    NEUTRO --> ADR

    ADR --> GFR[get_forward_return + get_ibovespa_return<br/>retorno real dos 5 pregões seguintes]
    GFR --> CSV2[(data/backtest_results*.csv)]
```

**Por que sem LLM:** narrativa em linguagem natural não agrega valor rodando centenas de vezes num loop histórico — o objetivo do backtest é medir a qualidade do sinal (RSI + MACD + sentimento), não a qualidade da explicação.

Decisões e trade-offs por trás de cada escolha acima (pipeline determinístico, migração para BigQuery, proteção contra look-ahead bias) estão detalhados em [`decisions.md`](decisions.md).
