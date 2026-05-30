"""Search Tool - search and browse GenPark-style products."""

from typing import Optional

from bot.catalog import rank_products


def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 10,
) -> dict:
    """
    Search for products using the local catalog.

    In production this function can be backed by a GenPark API or search index.
    The current implementation is deterministic so judges can run the workflow
    without private credentials.
    """
    if not query or not query.strip():
        return {
            "success": False,
            "message": "Please provide a search query.",
            "results": [],
            "count": 0,
        }

    results = rank_products(query, category=category, max_price=max_price, limit=limit)
    if not results:
        return {
            "success": True,
            "message": f"No products found matching '{query}'. Try different keywords.",
            "results": [],
            "count": 0,
        }

    return {
        "success": True,
        "message": f"Found {len(results)} products matching '{query}'.",
        "results": results,
        "count": len(results),
        "source": "local_catalog",
    }


def get_trending_products(
    category: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """Get top-rated products from the local catalog."""
    products = rank_products(category or "popular products", category=category, limit=limit)
    return {
        "success": True,
        "message": f"Here are the top {len(products)} trending products.",
        "products": products,
        "count": len(products),
        "source": "local_catalog",
    }
