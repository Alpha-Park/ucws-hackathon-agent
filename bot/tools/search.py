"""
Search Tool - Search and browse GenPark products.
"""

from typing import Optional

from ..browser.genpark_client import GenParkClient
from .recommend import SAMPLE_PRODUCTS  # Reuse sample data


def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 10,
) -> dict:
    """
    Search for products on GenPark.
    
    Use this when the user wants to find specific products or browse by keyword.
    
    Args:
        query: Search query string. Can be product names, keywords, or descriptions.
        category: Optional category filter.
        max_price: Optional maximum price filter.
        limit: Maximum number of results to return (default 10).
    
    Returns:
        A dict with 'success', 'results' (list of products), and 'count'.
    """
    if not query or not query.strip():
        return {
            "success": False,
            "message": "Please provide a search query.",
            "results": [],
            "count": 0
        }
    
    query_lower = query.lower()
    
    # Filter and search products
    results = []
    for product in SAMPLE_PRODUCTS:
        # Category filter
        if category and product["category"].lower() != category.lower():
            continue
        
        # Price filter
        if max_price and product["price"] > max_price:
            continue
        
        # Search in name, description, and tags
        searchable_text = f"{product['name']} {product['description']} {' '.join(product['tags'])}".lower()
        
        if query_lower in searchable_text:
            results.append(product)
    
    if not results:
        return {
            "success": True,
            "message": f"No products found matching '{query}'. Try different keywords.",
            "results": [],
            "count": 0
        }
    
    return {
        "success": True,
        "message": f"Found {len(results[:limit])} products matching '{query}':",
        "results": results[:limit],
        "count": len(results[:limit])
    }


def get_trending_products(
    category: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """
    Get currently trending and popular products on GenPark.
    
    Use this when the user wants to see what's popular, trending,
    or just browse without a specific query.
    
    Args:
        category: Optional category filter.
        limit: Maximum number of products to return (default 5).
    
    Returns:
        A dict with 'success', 'products' (list), and 'count'.
    """
    try:
        # In production, this would fetch from GenPark
        # For now, return highest-rated products
        products = SAMPLE_PRODUCTS.copy()
        
        # Category filter
        if category:
            products = [p for p in products if p["category"].lower() == category.lower()]
        
        # Sort by rating
        products.sort(key=lambda x: x["rating"], reverse=True)
        trending = products[:limit]
        
        if not trending:
            return {
                "success": True,
                "message": f"No trending products found in '{category}'.",
                "products": [],
                "count": 0
            }
        
        return {
            "success": True,
            "message": f"🔥 Here are the top {len(trending)} trending products:",
            "products": trending,
            "count": len(trending)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching trending products: {str(e)}",
            "products": [],
            "count": 0
        }
