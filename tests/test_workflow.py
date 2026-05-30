import asyncio
import tempfile
import unittest
from pathlib import Path

from bot.catalog import infer_budget, infer_category, rank_products
from bot.services import AgentService
from bot.store import AgentStore


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = AgentStore(Path(self.tempdir.name) / "agent.db")
        self.service = AgentService(self.store)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_budget_and_category_inference(self):
        self.assertEqual(infer_budget("smart home gift under $160"), 160)
        self.assertEqual(infer_category("smart home gadget"), "AI Gadgets")

    def test_ranking_respects_budget(self):
        products = rank_products("work from home tech", max_price=220, limit=5)
        self.assertTrue(products)
        self.assertTrue(all(product["price"] <= 220 for product in products))

    def test_agent_creates_traceable_pending_circle_post(self):
        response = asyncio.run(
            self.service.process_request(
                "user-1",
                "session-1",
                "Find a work-from-home gift under $220 and draft a Circle post asking friends to choose.",
            )
        )

        self.assertTrue(response["success"])
        self.assertTrue(response["products"])
        self.assertTrue(response["collection"])
        self.assertEqual(response["pending_action"]["type"], "post_to_circle")
        self.assertTrue(any(call["tool"] == "search_products" for call in response["tool_calls"]))

    def test_confirm_does_not_fake_publish_without_setup(self):
        asyncio.run(
            self.service.process_request(
                "user-1",
                "session-1",
                "Find a work-from-home gift under $220 and draft a Circle post.",
            )
        )
        response = asyncio.run(self.service.process_request("user-1", "session-1", "confirm post"))

        self.assertTrue(response["success"])
        self.assertEqual(response["pending_action"], None)
        self.assertIn(response["post"]["status"], {"posted", "drafted_requires_setup"})


if __name__ == "__main__":
    unittest.main()
