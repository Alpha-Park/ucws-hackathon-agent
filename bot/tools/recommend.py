"""Recommendation Tool - personalized product recommendations."""

from typing import Optional

from bot.catalog import PRODUCTS, rank_products

SAMPLE_PRODUCTS = PRODUCTS


def get_recommendations(
    preferences: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
) -> dict:
    """
    Get deterministic recommendations based on preferences.

    This keeps the hackathon demo reproducible while preserving a clear seam for
    a real GenPark catalog, vector search, or marketplace API.
    """
    if not preferences or not preferences.strip():
        return {
            "success": False,
            "message": "Please describe what kind of products you're looking for.",
            "recommendations": [],
            "count": 0,
        }

    recommendations = rank_products(
        preferences,
        category=category,
        max_price=max_price,
        limit=limit,
    )

    return {
        "success": True,
        "message": f"Found {len(recommendations)} products matching your preferences.",
        "recommendations": recommendations,
        "count": len(recommendations),
        "source": "local_catalog",
    }
