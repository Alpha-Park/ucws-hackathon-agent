"""Collection Management Tool - manage a user's product collection."""

from typing import Optional

from bot.catalog import PRODUCTS
from bot.store import AgentStore

_store = AgentStore()


def _find_product(product_id: str, product_name: str | None = None, product_url: str | None = None) -> dict:
    for product in PRODUCTS:
        if product["id"] == product_id:
            return dict(product)
    return {
        "id": product_id,
        "name": product_name or f"Product {product_id}",
        "product_url": product_url,
        "category": "Unknown",
        "price": 0,
        "description": "User-provided product.",
        "tags": [],
        "rating": 0,
    }


def add_to_collection(
    product_id: str,
    product_name: Optional[str] = None,
    product_url: Optional[str] = None,
    user_id: str = "default_user",
) -> dict:
    """Add a product to the local persisted collection."""
    if not product_id or not product_id.strip():
        return {"success": False, "message": "product_id is required"}

    product = _find_product(product_id, product_name, product_url)
    inserted = _store.add_to_collection(user_id, product)
    return {
        "success": True,
        "message": (
            f"Added '{product['name']}' to the local collection."
            if inserted
            else f"'{product['name']}' is already in the local collection."
        ),
        "mode": "local_persisted",
        "item": product,
    }


def list_collection(user_id: str = "default_user") -> dict:
    """List products in the local persisted collection."""
    items = _store.list_collection(user_id)
    return {
        "success": True,
        "message": f"Found {len(items)} items in the local collection.",
        "items": items,
        "count": len(items),
        "mode": "local_persisted",
    }


def remove_from_collection(product_id: str, user_id: str = "default_user") -> dict:
    """Remove a product from the local persisted collection."""
    removed = _store.remove_from_collection(user_id, product_id)
    return {
        "success": removed,
        "message": "Removed product from the local collection." if removed else "Product was not in the local collection.",
        "mode": "local_persisted",
    }
