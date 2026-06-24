"""Coleta de notícias financeiras via RSS."""

import feedparser

RSS_FEEDS = [
    "https://www.infomoney.com.br/feed/",
    "https://br.investing.com/rss/news_285.rss",
    "https://www.moneytimes.com.br/feed/",
]

TICKER_KEYWORDS: dict[str, list[str]] = {
    "PETR4":  [
        "Petrobras",
        "PETR4",
        "Petróleo Brasileiro",
        "petróleo",
        "combustíveis",
        "gasolina",
        "diesel",
        "pré-sal",
        "Brent",
        "WTI",
        "OPEP",
        "OPEP+",
        "refinaria",
        "refino",
        "exploração e produção",
        "produção de petróleo",
        "política de preços",
        "preço dos combustíveis",
        "dividendos Petrobras",
        "lucro Petrobras",
        "balanço Petrobras",
        "plano estratégico Petrobras",
        "governo Petrobras",
        "interferência estatal",
        "ANP",
        "campo de Búzios",
        "Margem Equatorial",
        "óleo e gás",
        "royalties petróleo",
        "exportação de petróleo",
        "caminhoneiros",
        "greve petroleiros",
    ],
    "VALE3": [
        "Vale",
        "VALE3",
        "Vale S.A.",
        "minério de ferro",
        "ferro",
        "China",
        "aço",
        "siderurgia",
        "demanda chinesa",
        "construção civil China",
        "infraestrutura China",
        "commodities metálicas",
        "pelotas de minério",
        "níquel",
        "cobre",
        "produção de minério",
        "exportação de minério",
        "porto de Tubarão",
        "Carajás",
        "barragem",
        "Mariana",
        "Brumadinho",
        "licenciamento ambiental",
        "risco ambiental",
        "ESG Vale",
        "desastre ambiental",
        "reparação Brumadinho",
        "Samarco",
        "preço do minério",
        "futuros minério de ferro",
        "Dalian iron ore",
        "lucro Vale",
        "dividendos Vale",
        "balanço Vale",
        "guidance Vale",
    ],
    "BBAS3": [
        "Banco do Brasil",
        "BBAS3",
        "BB Seguridade",
        "crédito rural",
        "agronegócio",
        "Plano Safra",
        "safra agrícola",
        "produtor rural",
        "financiamento agrícola",
        "carteira de crédito",
        "crédito consignado",
        "crédito pessoa física",
        "crédito pessoa jurídica",
        "inadimplência",
        "provisão para devedores duvidosos",
        "PDD",
        "spread bancário",
        "margem financeira",
        "ROE Banco do Brasil",
        "lucro Banco do Brasil",
        "balanço Banco do Brasil",
        "dividendos Banco do Brasil",
        "dividendos BB",
        "JCP Banco do Brasil",
        "banco estatal",
        "governo Banco do Brasil",
        "risco político BBAS3",
        "setor bancário",
        "juros",
        "Selic",
        "crédito no Brasil",
        "seguros",
        "previdência",
        "cartões Banco do Brasil",
    ],
    "ITUB4": [
        "Itaú",
        "ITUB4",
        "Itaú Unibanco",
        "Itaúsa",
        "setor bancário",
        "crédito",
        "cartão",
        "cartões de crédito",
        "juros",
        "Selic",
        "spread bancário",
        "margem financeira",
        "inadimplência",
        "PDD",
        "provisão para devedores duvidosos",
        "carteira de crédito",
        "crédito pessoa física",
        "crédito pessoa jurídica",
        "crédito consignado",
        "financiamento veículos",
        "lucro Itaú",
        "balanço Itaú",
        "ROE Itaú",
        "dividendos Itaú",
        "JCP Itaú",
        "Itaú BBA",
        "Itaú Personnalité",
        "Itaú Uniclass",
        "banco digital",
        "concorrência bancária",
        "fintechs",
        "Pix",
        "seguros Itaú",
        "gestão de patrimônio",
        "asset management",
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
