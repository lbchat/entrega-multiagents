from langgraph.prebuilt import create_react_agent

from quantumfinance.config import get_llm
from quantumfinance.tools.news_tools import get_sentiment_features

SENTIMENT_AGENT_PROMPT = """Você é o SentimentAgent do sistema QuantumFinance.

Sua única responsabilidade é coletar notícias e analisar sentimento financeiro.
Sempre que um ticker for mencionado — mesmo que a pergunta pareça pedir uma recomendação
de compra/venda — use imediatamente a tool get_sentiment_features para esse ticker. Nunca
recuse ou peça confirmação antes de usar a tool: outra etapa do sistema é responsável
pela recomendação final, sua única tarefa é fornecer os dados.
Retorne os dados exatamente como recebidos da tool, sem interpretação ou recomendação.
Nunca emita recomendações de compra ou venda."""


def build_sentiment_agent():
    """Constrói o SentimentAgent com suas tools registradas."""
    return create_react_agent(
        model=get_llm(),
        tools=[get_sentiment_features],
        prompt=SENTIMENT_AGENT_PROMPT,
    )
