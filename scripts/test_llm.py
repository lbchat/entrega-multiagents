from langchain_core.tools import tool
from quantumfinance.config import get_llm


@tool
def get_ticker_info(ticker: str) -> str:
    """Retorna uma descrição simples do ticker informado."""
    return f"Ticker {ticker} está sendo monitorado."


llm = get_llm()
llm_with_tools = llm.bind_tools([get_ticker_info])

response = llm_with_tools.invoke(
    "Use a tool disponível para buscar informações sobre PETR4."
)

print("Tipo de resposta:", type(response))
print("Tool calls:", response.tool_calls)
print("Conteúdo:", response.content)
