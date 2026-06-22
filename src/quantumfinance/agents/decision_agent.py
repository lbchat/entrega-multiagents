from enum import Enum

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, field_validator

from quantumfinance.config import get_llm


class Recommendation(str, Enum):
    COMPRAR = "COMPRAR"
    VENDER = "VENDER"
    AGUARDAR = "AGUARDAR"


class RecommendationOutput(BaseModel):
    ticker: str
    date: str                    # formato YYYY-MM-DD
    recommendation: Recommendation
    confidence: float            # 0.0 a 1.0
    rsi: float
    macd_signal: str
    sentiment_score: float
    sentiment_label: str
    top_headlines: list[str]
    reasoning: str

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Valida que a data está no formato YYYY-MM-DD."""
        from datetime import datetime
        datetime.strptime(v, "%Y-%m-%d")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Valida que a confiança está entre 0 e 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence deve estar entre 0.0 e 1.0")
        return v


DECISION_AGENT_PROMPT = """Você é o DecisionAgent do sistema QuantumFinance.

Sua responsabilidade é gerar recomendações fundamentadas de investimento.
Quando solicitado, use a tool generate_recommendation para o ticker informado.
Apresente o resultado de forma clara: recomendação, confiança, e os principais drivers da decisão.
Sempre explique o raciocínio em linguagem natural acessível ao usuário."""


def build_decision_agent():
    """Constrói o DecisionAgent com suas tools registradas."""
    from quantumfinance.tools.decision_tools import generate_recommendation

    return create_react_agent(
        model=get_llm(),
        tools=[generate_recommendation],
        prompt=DECISION_AGENT_PROMPT,
    )
