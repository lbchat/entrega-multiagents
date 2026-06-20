"""Testes do pipeline de sentimento."""

from quantumfinance.features.sentiment import aggregate_sentiment, classify_sentiment


def test_classify_sentiment_returns_valid_label():
    """Valida que a classificação retorna um dos três labels esperados."""
    result = classify_sentiment("A empresa teve excelentes resultados no trimestre")
    assert result["label"] in ("POSITIVO", "NEGATIVO", "NEUTRO")


def test_classify_sentiment_scores_sum_to_one():
    """Valida que os scores de probabilidade somam aproximadamente 1."""
    result = classify_sentiment("O mercado reagiu com cautela à notícia")
    total = sum(result["scores"].values())
    assert abs(total - 1.0) < 0.01


def test_aggregate_sentiment_empty_list():
    """Valida que lista vazia de notícias não quebra a agregação."""
    result = aggregate_sentiment([])
    assert result["sentiment_label"] == "NEUTRO"
    assert result["news_count"] == 0
    assert result["top_headlines"] == []


def test_aggregate_sentiment_has_required_keys():
    """Valida que a saída agregada tem todas as chaves obrigatórias."""
    news = [{"title": "Empresa anuncia recorde de lucros", "summary": "Resultado positivo no trimestre"}]
    result = aggregate_sentiment(news)
    required_keys = {"sentiment_score", "sentiment_label", "news_count", "top_headlines"}
    assert required_keys.issubset(result.keys())


def test_sentiment_score_in_valid_range():
    """Valida que o score agregado está sempre entre 0 e 1."""
    news = [{"title": "Notícia neutra sobre o mercado", "summary": ""}]
    result = aggregate_sentiment(news)
    assert 0.0 <= result["sentiment_score"] <= 1.0


def test_classify_sentiment_correct_polarity():
    """Valida que frases claramente positivas e negativas recebem o label correto.

    Protege contra regressão do bug de mapeamento de labels do FinBERT-PT-BR,
    onde id2label do modelo (POSITIVE/NEGATIVE/NEUTRAL) foi inicialmente
    associado na ordem errada às labels em português.
    """
    positive_result = classify_sentiment(
        "A empresa anunciou lucro recorde e forte crescimento no trimestre"
    )
    assert positive_result["label"] == "POSITIVO", (
        f"Esperado POSITIVO, obtido {positive_result['label']} "
        f"com scores {positive_result['scores']}"
    )

    negative_result = classify_sentiment(
        "A empresa anunciou prejuízo recorde e forte queda nas ações"
    )
    assert negative_result["label"] == "NEGATIVO", (
        f"Esperado NEGATIVO, obtido {negative_result['label']} "
        f"com scores {negative_result['scores']}"
    )
