"""
Collection Management Tool - Manage user's product collection.
"""

from typing import Optional

from ..browser.genpark_client import GenParkClient


# Local cache for collection (in production, this would be persisted)
_collection_cache: list[dict] = []


def add_to_collection(
    product_id: str,
    product_name: Optional[str] = None,
    product_url: Optional[str] = None,
) -> dict:
    """
    Add a product to the user's collection.
    
    Use this when the user wants to save a product for later or add it to their favorites.
    
    Args:
        product_id: The unique ID of the product to add.
        product_name: Optional name of the product for display purposes.
        product_url: Optional URL to the product page.
    
    Returns:
        A dict with 'success' (bool) and 'message' (str).
    """
    global _collection_cache
    
    # Check if already in collection
    for item in _collection_cache:
        if item.get("product_id") == product_id:
            return {
                "success": False,
                "message": f"Product '{product_name or product_id}' is already in your collection."
            }
    
    try:
        client = GenParkClient()
        result = client.add_to_collection(product_id)
        
        if result.get("success"):
            # Update local cache
            _collection_cache.append({
                "product_id": product_id,
                "product_name": product_name or f"Product {product_id}",
                "product_url": product_url,
            })
            
            return {
                "success": True,
                "message": f"✅ Added '{product_name or product_id}' to your collection!"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to add to collection: {result.get('error', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding to collection: {str(e)}"
        }


def list_collection() -> dict:
    """
    List all products in the user's collection.
    
    Use this when the user wants to see their saved products or favorites.
    
    Returns:
        A dict with 'success', 'items' (list of products), and 'count'.
    """
    try:
        client = GenParkClient()
        result = client.get_collection()
        
        if result.get("success"):
            items = result.get("items", [])
            
            if not items:
                return {
                    "success": True,
                    "message": "Your collection is empty. Start adding products you love!",
                    "items": [],
                    "count": 0
                }
            
            return {
                "success": True,
                "message": f"Found {len(items)} items in your collection.",
                "items": items,
                "count": len(items)
            }
        else:
            return {
                "success": False,
                "message": f"Failed to fetch collection: {result.get('error', 'Unknown error')}",
                "items": [],
                "count": 0
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error fetching collection: {str(e)}",
            "items": [],
            "count": 0
        }


def remove_from_collection(product_id: str) -> dict:
    """
    Remove a product from the user's collection.
    
    Use this when the user wants to remove a saved product.
    
    Args:
        product_id: The unique ID of the product to remove.
    
    Returns:
        A dict with 'success' (bool) and 'message' (str).
    """
    global _collection_cache
    
    try:
        client = GenParkClient()
        result = client.remove_from_collection(product_id)
        
        if result.get("success"):
            # Update local cache
            _collection_cache = [
                item for item in _collection_cache
                if item.get("product_id") != product_id
            ]
            
            return {
                "success": True,
                "message": f"✅ Removed product from your collection."
            }
        else:
            return {
                "success": False,
                "message": f"Failed to remove from collection: {result.get('error', 'Unknown error')}"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error removing from collection: {str(e)}"
        }
