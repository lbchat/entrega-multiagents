"""Coleta de notícias financeiras via RSS."""

import feedparser

RSS_FEEDS = [
    "https://www.infomoney.com.br/feed/",
    "https://valor.globo.com/rss/home/",
    "https://www.moneytimes.com.br/feed/",
]

TICKER_KEYWORDS: dict[str, list[str]] = {
    "PETR4": [
        "Petrobras", "PETR4", "petróleo", "combustíveis", "pré-sal",
        "Brent", "OPEP", "refinaria",
    ],
    "VALE3": [
        "Vale", "VALE3", "minério de ferro", "China", "aço",
        "barragem", "siderurgia",
    ],
    "BBAS3": [
        "Banco do Brasil", "BBAS3", "crédito rural", "agronegócio",
        "inadimplência",
    ],
    "ITUB4": [
        "Itaú", "ITUB4", "Itaú Unibanco", "crédito", "juros",
        "inadimplência",
    ],
}


def fetch_news(ticker: str, max_items: int = 15) -> list[dict]:
    """Coleta notícias de feeds RSS filtradas por keywords relevantes ao ticker."""
    keywords = TICKER_KEYWORDS.get(ticker, [ticker])
    keywords_lower = [k.lower() for k in keywords]

    collected: list[dict] = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue  # feed indisponível não deve quebrar o pipeline inteiro

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}".lower()

            if any(kw in text for kw in keywords_lower):
                collected.append({
                    "title": title,
                    "summary": summary,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed_url,
                })

        if len(collected) >= max_items:
            break

    return collected[:max_items]
