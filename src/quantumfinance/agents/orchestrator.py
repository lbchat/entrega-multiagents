"""Orquestrador principal do sistema QuantumFinance."""

from typing import Literal, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from quantumfinance.agents.context_router_agent import build_context_router_agent
from quantumfinance.agents.decision_agent import build_decision_agent
from quantumfinance.agents.diagnostic_agent import build_diagnostic_agent
from quantumfinance.agents.market_agent import build_market_agent
from quantumfinance.agents.sentiment_agent import build_sentiment_agent
from quantumfinance.config import get_llm
from quantumfinance.output.storage import save_recommendation
from quantumfinance.tools.decision_tools import generate_recommendation
from quantumfinance.tools.market_tools import get_market_features
from quantumfinance.tools.news_tools import get_sentiment_features
from quantumfinance.universe import MVP_TICKER, TICKERS

ROUTER_PROMPT = """Você é o roteador do sistema QuantumFinance.
Analise a pergunta do usuário e classifique em uma das categorias:
- "recommendation": usuário quer recomendação completa (COMPRAR/VENDER/AGUARDAR)
- "market": usuário quer só indicadores técnicos de um ticker
- "sentiment": usuário quer só sentimento/notícias de um ticker
- "diagnostic": usuário quer entender/explicar comportamento, comparar ativos, ou fazer pergunta aberta sobre o mercado
- "context": usuário pede análise contextual, de esferas temáticas, ou pergunta sobre fatores externos que afetam o ativo
Responda APENAS com uma dessas cinco palavras, sem explicação."""


class PipelineState(MessagesState):
    """Estado do grafo, estendido com os dados coletados no pipeline fixo."""

    ticker: Optional[str]
    market_features: Optional[dict]
    sentiment_features: Optional[dict]


def extract_ticker(text: str) -> str:
    """Identifica o ticker mencionado no texto, com fallback para o ticker do MVP."""
    text_upper = text.upper()
    for ticker in TICKERS:
        if ticker in text_upper:
            return ticker
    return MVP_TICKER


def build_graph():
    """Constrói e compila o grafo multiagente."""

    market_agent = build_market_agent()
    sentiment_agent = build_sentiment_agent()
    decision_agent = build_decision_agent()
    diagnostic_agent = build_diagnostic_agent()
    llm = get_llm()

    def route_intent(
        state: PipelineState,
    ) -> Literal["market_node", "sentiment_node", "diagnostic_node", "context_node", "pipeline_market"]:
        """Classifica a intenção da pergunta e roteia para o nó correto."""
        last_message = state["messages"][-1].content
        response = llm.invoke([
            HumanMessage(content=ROUTER_PROMPT),
            HumanMessage(content=f"Pergunta: {last_message}"),
        ])
        intent = response.content.strip().lower()

        if intent == "market":
            return "market_node"
        elif intent == "sentiment":
            return "sentiment_node"
        elif intent == "diagnostic":
            return "diagnostic_node"
        elif intent == "context":
            return "context_node"
        else:
            return "pipeline_market"  # padrão: pipeline completo

    def market_node(state: PipelineState) -> dict:
        """Nó do MarketAgent — responde perguntas pontuais sobre indicadores."""
        response = market_agent.invoke(state)
        return {"messages": response["messages"]}

    def sentiment_node(state: PipelineState) -> dict:
        """Nó do SentimentAgent — responde perguntas pontuais sobre sentimento."""
        response = sentiment_agent.invoke(state)
        return {"messages": response["messages"]}

    def diagnostic_node(state: PipelineState) -> dict:
        """Nó do DiagnosticAgent — investiga perguntas abertas com ReAct genuíno, sem pipeline fixo."""
        response = diagnostic_agent.invoke(state)
        return {"messages": response["messages"]}

    def context_node(state: PipelineState) -> dict:
        """Nó do ContextRouterAgent — analisa esferas temáticas do ativo via Asset Context Map.

        O agente é construído por requisição (não uma vez só, como os demais) porque
        seu prompt depende do ticker — precisa injetar as esferas reais do Asset Context
        Map antes de invocar o ReAct, para que o agente cite as esferas corretas mesmo
        quando não há cobertura de notícias no momento.
        """
        ticker = extract_ticker(str(state["messages"][-1].content))
        context_router_agent = build_context_router_agent(ticker)
        response = context_router_agent.invoke(state)
        return {"messages": response["messages"]}

    def pipeline_market(state: PipelineState) -> dict:
        """Primeiro passo do pipeline de recomendação: coleta dados de mercado.

        Chama a tool diretamente (sem passar por um LLM) porque esta etapa é
        determinística — o pipeline fixo não deve depender do LLM decidir
        usar a tool a cada vez.
        """
        ticker = extract_ticker(str(state["messages"][-1].content))
        market_features = get_market_features.invoke({"ticker": ticker})
        return {"ticker": ticker, "market_features": market_features}

    def pipeline_sentiment(state: PipelineState) -> dict:
        """Segundo passo do pipeline de recomendação: coleta sentimento."""
        sentiment_features = get_sentiment_features.invoke({"ticker": state["ticker"]})
        return {"sentiment_features": sentiment_features}

    def pipeline_decision(state: PipelineState) -> dict:
        """Terceiro passo do pipeline de recomendação: gera, persiste e narra a recomendação."""
        recommendation_data = generate_recommendation.invoke({"ticker": state["ticker"]})
        save_recommendation(recommendation_data)

        narration_request = (
            f"A recomendação para {state['ticker']} já foi calculada pelo sistema:\n"
            f"{recommendation_data}\n\n"
            "Apresente esse resultado ao usuário de forma clara, em linguagem natural: "
            "a recomendação, a confiança e os principais drivers (RSI, MACD, sentimento). "
            "Os dados já estão prontos acima — não chame nenhuma tool."
        )
        response = decision_agent.invoke({"messages": [HumanMessage(content=narration_request)]})
        return {"messages": [response["messages"][-1]]}

    # Construção do grafo
    graph = StateGraph(PipelineState)

    graph.add_node("market_node", market_node)
    graph.add_node("sentiment_node", sentiment_node)
    graph.add_node("diagnostic_node", diagnostic_node)
    graph.add_node("context_node", context_node)
    graph.add_node("pipeline_market", pipeline_market)
    graph.add_node("pipeline_sentiment", pipeline_sentiment)
    graph.add_node("pipeline_decision", pipeline_decision)

    graph.add_conditional_edges(
        START,
        route_intent,
        {
            "market_node": "market_node",
            "sentiment_node": "sentiment_node",
            "diagnostic_node": "diagnostic_node",
            "context_node": "context_node",
            "pipeline_market": "pipeline_market",
        }
    )

    graph.add_edge("market_node", END)
    graph.add_edge("sentiment_node", END)
    graph.add_edge("diagnostic_node", END)
    graph.add_edge("context_node", END)
    graph.add_edge("pipeline_market", "pipeline_sentiment")
    graph.add_edge("pipeline_sentiment", "pipeline_decision")
    graph.add_edge("pipeline_decision", END)

    return graph.compile()


# Instância global do grafo compilado
app = build_graph()


def ask(question: str) -> str:
    """Envia uma pergunta ao sistema e retorna a resposta final."""
    result = app.invoke({"messages": [HumanMessage(content=question)]})
    return result["messages"][-1].content
