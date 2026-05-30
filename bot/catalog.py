"""Product catalog utilities for search, ranking, and request parsing."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "products.json"

CATEGORY_KEYWORDS = {
    "AI Gadgets": {"ai", "assistant", "speaker", "voice", "gadget", "smart"},
    "Electronics": {"electronics", "charger", "audio", "earbuds", "wireless", "battery", "tech"},
    "Home & Living": {"home", "desk", "chair", "office", "vacuum", "cleaning", "living"},
    "Pet Supplies": {"pet", "pets", "dog", "cat", "feeder"},
    "Fashion": {"fashion", "wallet", "leather", "style", "rfid"},
    "Lifestyle": {"lifestyle", "garden", "plants", "indoor", "eco"},
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "best",
    "buy",
    "can",
    "circle",
    "community",
    "compare",
    "draft",
    "for",
    "find",
    "gift",
    "globally",
    "help",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "please",
    "post",
    "product",
    "products",
    "recommend",
    "save",
    "show",
    "shortlist",
    "some",
    "that",
    "the",
    "to",
    "under",
    "with",
    "within",
    "useful",
    "以内",
    "推荐",
    "帮我",
    "预算",
    "美元",
}


def load_products() -> list[dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


PRODUCTS = load_products()


def infer_budget(text: str) -> float | None:
    patterns = [
        r"(?:under|below|less than|max|maximum|budget|within)\s*\$?\s*(\d+(?:\.\d+)?)",
        r"\$\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:usd|dollars|sgd|美元|刀)",
        r"(?:预算|以内|不超过)\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def infer_category(text: str) -> str | None:
    words = set(tokenize(text))
    best_category = None
    best_score = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = len(words & keywords)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text.lower())
        if token not in STOP_WORDS and len(token) > 1
    ]


def product_text(product: dict[str, Any]) -> str:
    tags = " ".join(product.get("tags", []))
    return f"{product.get('name', '')} {product.get('category', '')} {product.get('description', '')} {tags}".lower()


def rank_products(
    query: str,
    *,
    category: str | None = None,
    max_price: float | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    tokens = tokenize(query)
    ranked: list[tuple[float, dict[str, Any]]] = []

    for product in PRODUCTS:
        if category and product["category"].lower() != category.lower():
            continue
        if max_price is not None and product["price"] > max_price:
            continue

        haystack = product_text(product)
        score = product.get("rating", 0) / 5
        matched_terms: list[str] = []

        for token in tokens:
            if token in haystack:
                score += 1.0
                matched_terms.append(token)

        if category and product["category"].lower() == category.lower():
            score += 0.75

        if max_price is not None:
            headroom = max_price - product["price"]
            if headroom >= 0:
                score += min(headroom / max_price, 0.15)

        if score > 0:
            enriched = dict(product)
            enriched["match_score"] = round(score, 3)
            enriched["why"] = build_reason(enriched, matched_terms, max_price)
            ranked.append((score, enriched))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [product for _, product in ranked[:limit]]


def build_reason(product: dict[str, Any], matched_terms: list[str], max_price: float | None) -> str:
    reasons = []
    if matched_terms:
        reasons.append(f"matches {', '.join(sorted(set(matched_terms)))}")
    if max_price is not None and product["price"] <= max_price:
        reasons.append(f"fits the ${max_price:g} budget")
    reasons.append(f"rated {product['rating']}/5")
    return "; ".join(reasons)


def summarize_products(products: list[dict[str, Any]]) -> str:
    if not products:
        return "I could not find a strong product match yet."
    lines = []
    for index, product in enumerate(products, 1):
        lines.append(
            f"{index}. {product['name']} (${product['price']:.2f}) - {product.get('why', product['description'])}"
        )
    return "\n".join(lines)
