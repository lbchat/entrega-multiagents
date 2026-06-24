"""Classificação de sentimento financeiro via FinBERT-PT-BR."""

from functools import lru_cache

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "lucas-leme/FinBERT-PT-BR"
HEADLINE_SUMMARY_EXCERPT_LENGTH = 100  # tamanho do trecho do resumo anexado à manchete


@lru_cache(maxsize=1)
def _load_model():
    """Carrega o tokenizer e modelo FinBERT-PT-BR uma única vez (cache em memória)."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def classify_sentiment(text: str) -> dict:
    """Classifica o sentimento de um texto financeiro em português."""
    tokenizer, model = _load_model()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    # labels do modelo (confirmado via AutoConfig.id2label): 0=POSITIVE, 1=NEGATIVE, 2=NEUTRAL
    labels = ["POSITIVO", "NEGATIVO", "NEUTRO"]
    scores = {label: round(float(probs[i]), 4) for i, label in enumerate(labels)}
    dominant_label = labels[int(torch.argmax(probs))]

    return {
        "label": dominant_label,
        "scores": scores,
        "confidence": round(float(torch.max(probs)), 4),
    }


def _format_headline(item: dict) -> str:
    """Anexa um trecho do resumo ao título quando ele agrega informação não visível no título sozinho."""
    title = item["title"]
    summary = item.get("summary", "").strip()

    if not summary or summary == title.strip():
        return title

    excerpt = summary[:HEADLINE_SUMMARY_EXCERPT_LENGTH].rstrip()
    if len(summary) > HEADLINE_SUMMARY_EXCERPT_LENGTH:
        excerpt += "..."

    return f"{title} — {excerpt}"


def aggregate_sentiment(news_items: list[dict]) -> dict:
    """Agrega o sentimento de uma lista de notícias em um score consolidado."""
    if not news_items:
        return {
            "sentiment_score": 0.5,
            "sentiment_label": "NEUTRO",
            "news_count": 0,
            "top_headlines": [],
        }

    classified = []
    for item in news_items:
        text = f"{item['title']} {item.get('summary', '')}"
        result = classify_sentiment(text)
        classified.append({**item, **result})

    # score consolidado: média de (positivo - negativo), normalizado para 0-1
    raw_scores = [
        c["scores"]["POSITIVO"] - c["scores"]["NEGATIVO"]
        for c in classified
    ]
    avg_raw = sum(raw_scores) / len(raw_scores)
    sentiment_score = round((avg_raw + 1) / 2, 4)  # normaliza de [-1,1] para [0,1]

    if sentiment_score > 0.6:
        sentiment_label = "POSITIVO"
    elif sentiment_score < 0.4:
        sentiment_label = "NEGATIVO"
    else:
        sentiment_label = "NEUTRO"

    top_headlines = [_format_headline(c) for c in classified[:3]]

    return {
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "news_count": len(classified),
        "top_headlines": top_headlines,
    }
