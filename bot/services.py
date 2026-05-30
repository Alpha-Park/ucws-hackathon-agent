"""Agent service orchestration for the GenPark social shopping workflow."""

from __future__ import annotations

import os
from typing import Any

from bot.catalog import infer_budget, infer_category, rank_products, summarize_products
from bot.store import AgentStore
from bot.tools.circle import post_to_circle
from bot.tools.search import search_products

APP_NAME = "ucws_social_shopping_agent"


class AgentService:
    """Runs a practical shopping-agent workflow with auditable tool traces."""

    def __init__(self, store: AgentStore | None = None):
        self.store = store or AgentStore()

    async def process_request(self, user_id: str, session_id: str, message: str) -> dict[str, Any]:
        clean_message = (message or "").strip()
        if not clean_message:
            return {
                "success": False,
                "error": "message is required",
                "mode": "local_operator",
            }

        self.store.touch_session(user_id, session_id, last_message=clean_message)
        pending_action = self.store.get_pending_action(user_id, session_id)

        if pending_action and self._is_confirmation(clean_message):
            response = self._execute_pending_action(user_id, session_id, pending_action)
        elif self._is_collection_request(clean_message):
            response = self._show_collection(user_id)
        else:
            response = self._run_shopping_workflow(user_id, session_id, clean_message)

        self.store.save_trace(user_id, session_id, clean_message, response)
        return response

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "app_name": APP_NAME,
            "mode": "local_operator",
            "store": str(self.store.db_path),
            "genpark_browser_enabled": bool(os.getenv("GENPARK_EMAIL") and os.getenv("GENPARK_PASSWORD")),
        }

    def _run_shopping_workflow(self, user_id: str, session_id: str, message: str) -> dict[str, Any]:
        budget = infer_budget(message)
        inferred_category = infer_category(message)
        category = inferred_category
        wants_circle = self._wants_circle_post(message)

        plan = [
            "Parse the shopping intent, budget, and category hints.",
            "Search the product catalog with budget-aware ranking.",
            "Compare candidates and explain the tradeoffs.",
            "Save the strongest shortlist to the user's collection.",
            "Draft a Circle post and wait for explicit confirmation before publishing.",
        ]

        tool_calls: list[dict[str, Any]] = []

        search_result = search_products(
            query=message,
            category=category,
            max_price=budget,
            limit=5,
        )
        products = search_result.get("results", [])
        tool_calls.append(
            {
                "tool": "search_products",
                "input": {"query": message, "category": category, "max_price": budget, "limit": 5},
                "status": "completed",
                "summary": f"{len(products)} candidates found",
            }
        )

        if not products:
            products = rank_products(message, max_price=budget, limit=5)
            category = None
            tool_calls.append(
                {
                    "tool": "fallback_rank_products",
                    "input": {"query": message, "max_price": budget, "limit": 5},
                    "status": "completed",
                    "summary": f"{len(products)} fallback candidates ranked after relaxing category",
                }
            )

        saved_count = 0
        for product in products[:3]:
            if self.store.add_to_collection(user_id, product):
                saved_count += 1
        tool_calls.append(
            {
                "tool": "save_to_collection",
                "input": {"user_id": user_id, "product_ids": [p["id"] for p in products[:3]]},
                "status": "completed",
                "summary": f"{saved_count} new items saved locally",
            }
        )

        draft_post = self._draft_circle_post(message, products)
        pending_action = None
        if wants_circle:
            pending_action = {
                "type": "post_to_circle",
                "content": draft_post,
                "products": products[:3],
            }
            self.store.set_pending_action(user_id, session_id, pending_action)
            tool_calls.append(
                {
                    "tool": "draft_circle_post",
                    "input": {"requires_confirmation": True},
                    "status": "awaiting_confirmation",
                    "summary": "Circle post drafted but not published",
                }
            )

        answer = self._build_answer(products, budget, category, wants_circle)

        return {
            "success": True,
            "mode": "local_operator",
            "user_id": user_id,
            "session_id": session_id,
            "answer": answer,
            "plan": plan,
            "tool_calls": tool_calls,
            "constraints": {"budget": budget, "category": category, "inferred_category": inferred_category},
            "products": products,
            "collection": self.store.list_collection(user_id),
            "draft_post": draft_post,
            "pending_action": pending_action,
            "next_action": "Reply `confirm post` to publish the Circle draft." if wants_circle else "Ask for a Circle post when you want a shareable draft.",
        }

    def _execute_pending_action(
        self,
        user_id: str,
        session_id: str,
        pending_action: dict[str, Any],
    ) -> dict[str, Any]:
        if pending_action.get("type") != "post_to_circle":
            self.store.clear_pending_action(user_id, session_id)
            return {
                "success": False,
                "mode": "local_operator",
                "error": "Unknown pending action was cleared.",
            }

        content = pending_action["content"]
        result = post_to_circle(content)
        posted = bool(result.get("success"))
        status = "posted" if posted else "drafted_requires_setup"
        post_id = self.store.save_post(user_id, content, status, result.get("post_url"))
        self.store.clear_pending_action(user_id, session_id)

        if posted:
            answer = "Confirmed. The Circle post was published and recorded in the local audit log."
        else:
            answer = (
                "I saved the approved Circle draft, but did not claim it was posted because GenPark "
                "browser credentials or Playwright are not fully configured."
            )

        return {
            "success": True,
            "mode": "local_operator",
            "answer": answer,
            "post": {
                "id": post_id,
                "status": status,
                "content": content,
                "post_url": result.get("post_url"),
                "details": result,
            },
            "tool_calls": [
                {
                    "tool": "post_to_circle",
                    "status": "completed" if posted else "requires_setup",
                    "summary": result.get("message") or result.get("error", "Circle post did not publish"),
                }
            ],
            "pending_action": None,
        }

    def _show_collection(self, user_id: str) -> dict[str, Any]:
        collection = self.store.list_collection(user_id)
        return {
            "success": True,
            "mode": "local_operator",
            "answer": f"You have {len(collection)} saved products in this local collection.",
            "products": collection,
            "collection": collection,
            "tool_calls": [
                {
                    "tool": "list_collection",
                    "status": "completed",
                    "summary": f"{len(collection)} items returned",
                }
            ],
            "pending_action": None,
        }

    @staticmethod
    def _is_confirmation(message: str) -> bool:
        normalized = message.lower().strip()
        return normalized in {"confirm", "confirm post", "yes", "yes post it", "publish", "post it", "确认", "发布"}

    @staticmethod
    def _is_collection_request(message: str) -> bool:
        normalized = message.lower()
        return any(phrase in normalized for phrase in ["my collection", "saved products", "list collection", "我的收藏", "收藏列表"])

    @staticmethod
    def _wants_circle_post(message: str) -> bool:
        normalized = message.lower()
        return any(token in normalized for token in ["circle", "post", "share", "发帖", "发布", "朋友圈"])

    @staticmethod
    def _draft_circle_post(message: str, products: list[dict[str, Any]]) -> str:
        if not products:
            return "I am still looking for the right products. What budget, recipient, or use case should I optimize for?"

        names = ", ".join(product["name"] for product in products[:3])
        return (
            "I am comparing a shortlist for this shopping need: "
            f"{message}\n\n"
            f"Top candidates: {names}.\n"
            "Which one would you pick, and what tradeoff should I check before buying? #GenPark #SocialShopping"
        )

    @staticmethod
    def _build_answer(
        products: list[dict[str, Any]],
        budget: float | None,
        category: str | None,
        wants_circle: bool,
    ) -> str:
        context = []
        if budget is not None:
            context.append(f"budget ${budget:g}")
        if category:
            context.append(category)
        context_text = f" for {' and '.join(context)}" if context else ""

        answer = f"I found a ranked shortlist{context_text}:\n{summarize_products(products)}"
        if products:
            answer += "\n\nI saved the top candidates to the local collection so the workflow is reproducible."
        if wants_circle:
            answer += "\n\nI also drafted a Circle post and am waiting for explicit confirmation before publishing."
        return answer
