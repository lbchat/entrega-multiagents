"""Roteamento de notícias por esfera contextual do Asset Context Map."""

from pathlib import Path

import yaml

CONTEXT_MAP_PATH = Path(__file__).parent / "context_map.yaml"


def _load_context_map() -> dict:
    """Carrega o Asset Context Map do YAML."""
    with open(CONTEXT_MAP_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_context_keywords(ticker: str) -> dict[str, list[str]]:
    """Retorna as esferas e keywords cadastradas para o ticker no Asset Context Map."""
    context_map = _load_context_map()
    ticker_data = context_map.get(ticker)
    if ticker_data is None:
        return {}

    return {
        sphere: sphere_data["keywords"]
        for sphere, sphere_data in ticker_data["spheres"].items()
    }


def route_context_search(ticker: str, news_items: list[dict]) -> dict[str, list[dict]]:
    """Classifica notícias já coletadas nas esferas do ticker, por keyword match.

    Uma notícia pode aparecer em múltiplas esferas se tiver keywords de mais de uma.
    """
    sphere_keywords = get_context_keywords(ticker)
    result: dict[str, list[dict]] = {}

    for sphere, keywords in sphere_keywords.items():
        keywords_lower = [kw.lower() for kw in keywords]
        matched_news = [
            item
            for item in news_items
            if any(
                kw in f"{item.get('title', '')} {item.get('summary', '')}".lower()
                for kw in keywords_lower
            )
        ]
        if matched_news:
            result[sphere] = matched_news

    return result
