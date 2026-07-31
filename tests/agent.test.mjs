import assert from "node:assert/strict";
import test from "node:test";

import { inferBudget, rankProducts } from "../lib/catalog.js";
import { health, processRequest } from "../lib/agent.js";
import { publicCapabilities } from "../lib/toolRegistry.js";

test("infers budget from shopping prompt", () => {
  assert.equal(inferBudget("Find a gift under $220"), 220);
});

test("ranks remote worker products within budget", () => {
  const products = rankProducts("remote worker gift under $220", { maxPrice: 220, limit: 3 });
  assert.ok(products.length > 0);
  assert.ok(products.every((product) => product.price <= 220));
  assert.equal(products[0].id, "prod_007");
});

test("broadens narrow category results for work-from-home gift prompts", async () => {
  const response = await processRequest({
    userId: `test_user_${Date.now()}_broad`,
    sessionId: "ranking",
    message:
      "Find a work-from-home gift under $220 and draft a Circle post asking friends to choose.",
  });

  assert.equal(response.constraints.budget, 220);
  assert.equal(response.constraints.inferred_category, "Home & Living");
  assert.equal(response.constraints.category, null);
  assert.ok(response.tool_calls.some((call) => call.tool === "broaden_product_search"));
  assert.equal(response.products[0].id, "prod_007");
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
  assert.ok(first.run_id.startsWith("run_"));
  assert.ok(first.scorecard.overall >= 80);
  assert.ok(first.safety_checks.some((check) => check.status === "armed_requires_approval"));
  assert.ok(first.decision_log.some((entry) => entry.includes("External publishing")));
  assert.ok(first.capabilities.tools.some((tool) => tool.name === "post_to_circle"));

  const second = await processRequest({
    userId,
    sessionId,
    message: "confirm post",
  });
  assert.equal(second.pending_action, null);
  assert.equal(second.post.status, "drafted_requires_setup");
  assert.ok(second.safety_checks.some((check) => check.name === "No fake side effects"));
});

test("publishes a public capability contract", () => {
  const capabilities = publicCapabilities();
  const toolNames = capabilities.tools.map((tool) => tool.name);

  assert.equal(capabilities.autonomy_model, "supervised_operator");
  assert.ok(toolNames.includes("self_evaluate_run"));
  assert.ok(toolNames.includes("post_to_circle"));
  assert.equal(health().agent_card.tool_count, capabilities.tools.length);
});
