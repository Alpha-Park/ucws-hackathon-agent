import assert from "node:assert/strict";
import test from "node:test";

import { inferBudget, rankProducts } from "../lib/catalog.js";
import { processRequest } from "../lib/agent.js";

test("infers budget from shopping prompt", () => {
  assert.equal(inferBudget("Find a gift under $220"), 220);
});

test("ranks remote worker products within budget", () => {
  const products = rankProducts("remote worker gift under $220", { maxPrice: 220, limit: 3 });
  assert.ok(products.length > 0);
  assert.ok(products.every((product) => product.price <= 220));
  assert.equal(products[0].id, "prod_007");
});

test("creates pending Circle approval and does not fake publish", async () => {
  const userId = `test_user_${Date.now()}`;
  const sessionId = "approval";

  const first = await processRequest({
    userId,
    sessionId,
    message: "Find a work-from-home gift under $220 and draft a Circle post.",
  });
  assert.equal(first.pending_action?.type, "post_to_circle");
  assert.ok(first.draft_post.includes("Top candidates"));

  const second = await processRequest({
    userId,
    sessionId,
    message: "confirm post",
  });
  assert.equal(second.pending_action, null);
  assert.equal(second.post.status, "drafted_requires_setup");
});
