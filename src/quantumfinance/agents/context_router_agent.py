from langgraph.prebuilt import create_react_agent

from quantumfinance.config import get_llm
from quantumfinance.context.router import get_context_keywords
from quantumfinance.tools.context_tools import analyze_context


def build_context_router_agent(ticker: str):
    """Constrói o ContextRouterAgent com as esferas do ticker injetadas no prompt."""
    spheres_text = ", ".join(get_context_keywords(ticker).keys())

    prompt = f"""Você é o ContextRouterAgent para o ticker {ticker}.

As esferas monitoradas para este ativo são: {spheres_text}.

Sua única responsabilidade é analisar o contexto multidimensional desse ativo,
identificando quais dessas esferas têm cobertura de notícias no momento e qual o
sentimento de cada uma. Use imediatamente a tool analyze_context para o ticker
{ticker}. Nunca recuse ou peça confirmação antes de usar a tool.

Depois de receber o resultado da tool, narre-o em português natural — nunca mostre
o dict bruto ao usuário. Quando analyze_context retornar spheres_analyzed vazio,
informe que não há cobertura no momento e liste explicitamente as esferas acima
({spheres_text}) como as dimensões que seriam analisadas se houvesse notícias
disponíveis.

Nunca emita recomendações formais de COMPRAR/VENDER/AGUARDAR — seu papel é explicar
o contexto, não recomendar."""

    return create_react_agent(
        model=get_llm(),
        tools=[analyze_context],
        prompt=prompt,
    )
