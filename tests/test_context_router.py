"""Testes do Context Router (Asset Context Map)."""

from quantumfinance.context.router import get_context_keywords, route_context_search


def test_get_context_keywords_returns_spheres_for_known_ticker():
    """Valida que as esferas e keywords do ticker conhecido são retornadas."""
    result = get_context_keywords("PETR4")
    assert "energy" in result
    assert "politics_regulation" in result
    assert len(result["energy"]) > 0


def test_get_context_keywords_returns_empty_for_unknown_ticker():
    """Valida que um ticker fora do Asset Context Map retorna dict vazio."""
    result = get_context_keywords("TICKER_INEXISTENTE")
    assert result == {}


def test_route_context_search_classifies_news():
    """Valida que notícias são classificadas na esfera correta por keyword match."""
    news = [
        {"title": "Petrobras anuncia nova política de preços de combustíveis", "summary": ""},
        {"title": "OPEP reduz produção de petróleo Brent sobe", "summary": ""},
    ]
    result = route_context_search("PETR4", news)
    assert "politics_regulation" in result or "energy" in result
