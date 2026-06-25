from langgraph.prebuilt import create_react_agent

from quantumfinance.config import get_llm
from quantumfinance.tools.decision_tools import generate_recommendation
from quantumfinance.tools.market_tools import get_market_features
from quantumfinance.tools.news_tools import get_sentiment_features

DIAGNOSTIC_AGENT_PROMPT = """Você é o DiagnosticAgent do sistema QuantumFinance.

Sua função é investigar e explicar comportamentos de ativos brasileiros.
Você tem acesso a dados de mercado, indicadores técnicos e sentimento de notícias.
Use quantas tools forem necessárias para responder com profundidade. Raciocine passo
a passo antes de concluir. Nunca emita recomendações formais de COMPRAR/VENDER/AGUARDAR
— seu papel é explicar, não recomendar."""


def build_diagnostic_agent():
    """Constrói o DiagnosticAgent com acesso a todas as tools do sistema."""
    return create_react_agent(
        model=get_llm(),
        tools=[get_market_features, get_sentiment_features, generate_recommendation],
        prompt=DIAGNOSTIC_AGENT_PROMPT,
    )
