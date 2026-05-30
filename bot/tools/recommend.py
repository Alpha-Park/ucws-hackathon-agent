"""
Recommendation Tool - Personalized product recommendations.
"""

from typing import Optional

# Sample product database (in production, this would come from GenPark API)
SAMPLE_PRODUCTS = [
    {
        "id": "prod_001",
        "name": "AI Smart Speaker Pro",
        "category": "AI Gadgets",
        "price": 149.99,
        "description": "Voice-controlled smart speaker with advanced AI assistant",
        "tags": ["smart home", "ai", "speaker", "voice control"],
        "rating": 4.7,
    },
    {
        "id": "prod_002",
        "name": "Portable Solar Charger",
        "category": "Electronics",
        "price": 79.99,
        "description": "Eco-friendly solar power bank for outdoor adventures",
        "tags": ["eco-friendly", "outdoor", "charger", "portable"],
        "rating": 4.5,
    },
    {
        "id": "prod_003",
        "name": "Ergonomic Desk Chair",
        "category": "Home & Living",
        "price": 299.99,
        "description": "Premium ergonomic chair with lumbar support",
        "tags": ["office", "ergonomic", "chair", "work from home"],
        "rating": 4.8,
    },
    {
        "id": "prod_004",
        "name": "Smart Pet Feeder",
        "category": "Pet Supplies",
        "price": 89.99,
        "description": "Automated pet feeder with app control and camera",
        "tags": ["pet", "smart home", "automated", "feeding"],
        "rating": 4.6,
    },
    {
        "id": "prod_005",
        "name": "Minimalist Leather Wallet",
        "category": "Fashion",
        "price": 49.99,
        "description": "Slim RFID-blocking leather wallet",
        "tags": ["fashion", "wallet", "leather", "minimalist"],
        "rating": 4.4,
    },
    {
        "id": "prod_006",
        "name": "Robot Vacuum Cleaner",
        "category": "Home & Living",
        "price": 399.99,
        "description": "AI-powered robot vacuum with mapping and scheduling",
        "tags": ["smart home", "cleaning", "robot", "automated"],
        "rating": 4.7,
    },
    {
        "id": "prod_007",
        "name": "Wireless Noise-Canceling Earbuds",
        "category": "Electronics",
        "price": 199.99,
        "description": "Premium earbuds with ANC and 30-hour battery life",
        "tags": ["audio", "wireless", "noise-canceling", "earbuds"],
        "rating": 4.8,
    },
    {
        "id": "prod_008",
        "name": "Smart Garden Kit",
        "category": "Lifestyle",
        "price": 129.99,
        "description": "Indoor smart garden with automated watering and LED grow lights",
        "tags": ["garden", "smart home", "plants", "indoor"],
        "rating": 4.5,
    },
]


def get_recommendations(
    preferences: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
) -> dict:
    """
    Get personalized product recommendations based on user preferences.
    
    Use this when the user asks for product suggestions, recommendations,
    or help finding products that match their needs.
    
    Args:
        preferences: Description of what the user is looking for.
                    Examples: "smart home gadgets", "eco-friendly products",
                    "gifts for tech lovers", "work from home essentials"
        category: Optional category filter. Options: "AI Gadgets", "Electronics",
                 "Home & Living", "Pet Supplies", "Fashion", "Lifestyle"
        max_price: Optional maximum price filter.
        limit: Maximum number of recommendations to return (default 5).
    
    Returns:
        A dict with 'success', 'recommendations' (list of products), and 'count'.
    """
    if not preferences or not preferences.strip():
        return {
            "success": False,
            "message": "Please describe what kind of products you're looking for.",
            "recommendations": [],
            "count": 0
        }
    
    # Normalize preferences for matching
    pref_lower = preferences.lower()
    pref_words = set(pref_lower.split())
    
    # Score and filter products
    scored_products = []
    for product in SAMPLE_PRODUCTS:
        # Category filter
        if category and product["category"].lower() != category.lower():
            continue
        
        # Price filter
        if max_price and product["price"] > max_price:
            continue
        
        # Calculate relevance score based on tag and description matching
        score = 0
        product_text = f"{product['name']} {product['description']} {' '.join(product['tags'])}".lower()
        
        for word in pref_words:
            if word in product_text:
                score += 1
        
        # Boost score by rating
        score += product["rating"] / 5.0
        
        if score > 0:
            scored_products.append((score, product))
    
    # Sort by score and take top N
    scored_products.sort(key=lambda x: x[0], reverse=True)
    recommendations = [p for _, p in scored_products[:limit]]
    
    if not recommendations:
        # Return some defaults if no matches
        recommendations = SAMPLE_PRODUCTS[:limit]
        message = f"Here are some popular products you might like:"
    else:
        message = f"Found {len(recommendations)} products matching your preferences:"
    
    return {
        "success": True,
        "message": message,
        "recommendations": recommendations,
        "count": len(recommendations)
    }
