import { inferBudget, inferCategory, rankProducts, summarizeProducts } from "./catalog.js";
import {
  buildAgentCard,
  buildClarifyingQuestions,
  buildDecisionLog,
  buildNextActions,
  buildObjective,
  buildObservations,
  buildSafetyChecks,
  buildScorecard,
  createRunId,
} from "./agentIntelligence.js";
import {
  addToCollection,
  clearPendingAction,
  getPendingAction,
  listCollection,
  savePost,
  saveTrace,
  setPendingAction,
  storeStats,
  touchSession,
} from "./store.js";
import { publicCapabilities } from "./toolRegistry.js";

const APP_NAME = "ucws_social_shopping_agent";

export function health() {
  return {
    status: "ok",
    app_name: APP_NAME,
    mode: "vercel_operator",
    runtime: "nextjs",
    store: "serverless_memory",
    circle_publish_enabled: Boolean(process.env.GENPARK_CIRCLE_WEBHOOK_URL),
    agent_card: buildAgentCard(),
    stats: storeStats(),
  };
}

export async function processRequest({ userId, sessionId, message }) {
  const cleanMessage = String(message || "").trim();

  if (!cleanMessage) {
    return {
      success: false,
      error: "message is required",
      mode: "vercel_operator",
    };
  }

  touchSession(userId, sessionId, { lastMessage: cleanMessage });
  const pendingAction = getPendingAction(userId, sessionId);

  let response;
  if (pendingAction && isConfirmation(cleanMessage)) {
    response = await executePendingAction(userId, sessionId, pendingAction);
  } else if (isCollectionRequest(cleanMessage)) {
    response = showCollection(userId);
  } else {
    response = runShoppingWorkflow(userId, sessionId, cleanMessage);
  }

  saveTrace(userId, sessionId, cleanMessage, response);
  return response;
}

function runShoppingWorkflow(userId, sessionId, message) {
  const runId = createRunId();
  const budget = inferBudget(message);
  const inferredCategory = inferCategory(message);
  let category = inferredCategory;
  const wantsCircle = wantsCirclePost(message);
  const circleEnabled = Boolean(process.env.GENPARK_CIRCLE_WEBHOOK_URL);

  const plan = [
    "Build an execution brief with constraints, assumptions, and success criteria.",
    "Parse the shopping intent, budget, and category hints.",
    "Search the product catalog with budget-aware ranking.",
    "Compare candidates and explain the tradeoffs.",
    "Save the strongest shortlist to the user's collection.",
    "Draft an approval-gated Circle community handoff and wait for explicit confirmation.",
  ];

  const toolCalls = [];
  toolCalls.push({
    tool: "parse_intent",
    input: { message },
    status: "completed",
    summary: `Budget ${budget === null ? "not specified" : `$${budget}`}; category ${
      category || "broad"
    }; Circle handoff ${wantsCircle ? "requested" : "not requested"}`,
  });

  let products = rankProducts(message, {
    category,
    maxPrice: budget,
    limit: 5,
  });

  toolCalls.push({
    tool: "search_products",
    input: { query: message, category, max_price: budget, limit: 5 },
    status: "completed",
    summary: `${products.length} candidates found`,
  });

  if (products.length < 3) {
    const broaderProducts = rankProducts(message, { maxPrice: budget, limit: 5 });
    const seenProductIds = new Set(products.map((product) => product.id));
    products = [
      ...products,
      ...broaderProducts.filter((product) => !seenProductIds.has(product.id)),
    ].slice(0, 5);
    category = null;
    toolCalls.push({
      tool: "broaden_product_search",
      input: { query: message, max_price: budget, limit: 5 },
      status: "completed",
      summary: `${products.length} candidates ranked after relaxing narrow category constraints`,
    });
  }

  let savedCount = 0;
  for (const product of products.slice(0, 3)) {
    if (addToCollection(userId, product)) savedCount += 1;
  }
  toolCalls.push({
    tool: "save_to_collection",
    input: { user_id: userId, product_ids: products.slice(0, 3).map((product) => product.id) },
    status: "completed",
    summary: `${savedCount} new items saved in the demo collection`,
  });

  const draftPost = draftCirclePost(message, products);
  let pendingAction = null;
  if (wantsCircle) {
    pendingAction = {
      type: "post_to_circle",
      content: draftPost,
      products: products.slice(0, 3),
    };
    setPendingAction(userId, sessionId, pendingAction);
    toolCalls.push({
      tool: "draft_circle_post",
      input: { requires_confirmation: true },
      status: "awaiting_confirmation",
      summary: "Approval-gated Circle handoff drafted",
    });
  }

  const collection = listCollection(userId);
  const objective = buildObjective(message, { budget, category, wantsCircle });
  const observations = buildObservations({ budget, category, products, collection });
  const decisionLog = buildDecisionLog({ products, savedCount, wantsCircle, pendingAction });
  const safetyChecks = buildSafetyChecks({ wantsCircle, pendingAction, circleEnabled });
  const clarifyingQuestions = buildClarifyingQuestions({ budget, category, products });
  const scorecard = buildScorecard({
    budget,
    products,
    savedCount,
    wantsCircle,
    pendingAction,
    circleEnabled,
  });
  const nextActions = buildNextActions({ pendingAction, clarifyingQuestions });

  toolCalls.push({
    tool: "self_evaluate_run",
    input: { run_id: runId },
    status: scorecard.overall >= 80 ? "completed" : "needs_more_context",
    summary: `Operator readiness ${scorecard.overall}/100; ${clarifyingQuestions.length} follow-up question${clarifyingQuestions.length === 1 ? "" : "s"}`,
  });

  return {
    success: true,
    run_id: runId,
    mode: "vercel_operator",
    user_id: userId,
    session_id: sessionId,
    answer: buildAnswer(products, budget, category, wantsCircle),
    plan,
    tool_calls: toolCalls,
    objective,
    observations,
    decision_log: decisionLog,
    safety_checks: safetyChecks,
    clarifying_questions: clarifyingQuestions,
    next_actions: nextActions,
    scorecard,
    agent_card: buildAgentCard(),
    capabilities: publicCapabilities(),
    constraints: { budget, category, inferred_category: inferredCategory },
    products,
    collection,
    draft_post: draftPost,
    pending_action: pendingAction,
    next_action: wantsCircle
      ? "Reply `confirm post` to approve the Circle draft. The hosted demo records approved drafts unless a Circle publishing webhook is configured."
      : "Ask for a Circle handoff when you want a shareable community draft.",
  };
}

async function executePendingAction(userId, sessionId, pendingAction) {
  const runId = createRunId();
  if (pendingAction.type !== "post_to_circle") {
    clearPendingAction(userId, sessionId);
    return {
      success: false,
      mode: "vercel_operator",
      error: "Unknown pending action was cleared.",
    };
  }

  const result = await postToCircle(pendingAction.content);
  const posted = Boolean(result.success);
  const status = posted ? "posted" : "drafted_requires_setup";
  const post = savePost(userId, pendingAction.content, status, result.post_url || null, result);
  clearPendingAction(userId, sessionId);

  return {
    success: true,
    run_id: runId,
    mode: "vercel_operator",
    answer: posted
      ? "Confirmed. The approved Circle handoff was published and recorded in the audit log."
      : "I saved the approved Circle handoff draft, but did not claim it was posted because no Circle publishing webhook is configured for this Vercel demo.",
    post: {
      id: post.id,
      status: post.status,
      content: post.content,
      post_url: post.post_url,
      details: result,
    },
    tool_calls: [
      {
        tool: "post_to_circle",
        status: posted ? "completed" : "requires_setup",
        summary: result.message || result.error || "Circle post did not publish",
      },
      {
        tool: "self_evaluate_run",
        status: posted ? "completed" : "needs_setup",
        summary: posted
          ? "Approved side effect completed."
          : "Approved draft recorded without claiming an external post.",
      },
    ],
    safety_checks: buildSafetyChecks({
      wantsCircle: true,
      pendingAction: null,
      circleEnabled: Boolean(process.env.GENPARK_CIRCLE_WEBHOOK_URL),
    }),
    next_actions: posted
      ? ["Open the published post URL.", "Use the saved collection as the decision record."]
      : ["Configure GENPARK_CIRCLE_WEBHOOK_URL for real publishing.", "Keep the approved draft as the audit record."],
    scorecard: {
      overall: posted ? 100 : 80,
      label: posted ? "operator_ready" : "setup_required",
      checks: [
        {
          label: "Approval received",
          passed: true,
          detail: "The user explicitly confirmed the draft.",
        },
        {
          label: "No fake publish",
          passed: true,
          detail: posted ? "External publish completed." : "Missing setup was disclosed.",
        },
      ],
    },
    pending_action: null,
  };
}

function showCollection(userId) {
  const collection = listCollection(userId);
  return {
    success: true,
    run_id: createRunId(),
    mode: "vercel_operator",
    answer: `You have ${collection.length} saved products in this demo collection.`,
    products: collection,
    collection,
    tool_calls: [
      {
        tool: "list_collection",
        status: "completed",
        summary: `${collection.length} items returned`,
      },
    ],
    pending_action: null,
    next_actions: collection.length
      ? ["Ask for a tradeoff comparison across saved products.", "Draft a Circle post from the collection."]
      : ["Run a shopping prompt first so the agent can save a shortlist."],
  };
}

async function postToCircle(content) {
  const webhookUrl = process.env.GENPARK_CIRCLE_WEBHOOK_URL;
  if (!webhookUrl) {
    return {
      success: false,
      requires_setup: true,
      message:
        "No GENPARK_CIRCLE_WEBHOOK_URL is configured. The hosted demo records the approved draft without faking a publish.",
      content,
    };
  }

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    return {
      success: false,
      error: `Circle webhook returned ${response.status}`,
      content,
    };
  }

  const data = await response.json().catch(() => ({}));
  return {
    success: true,
    message: "Circle webhook accepted the approved handoff.",
    post_url: data.post_url || data.url || null,
  };
}

function isConfirmation(message) {
  return new Set(["confirm", "confirm post", "yes", "yes post it", "publish", "post it"]).has(
    message.toLowerCase().trim()
  );
}

function isCollectionRequest(message) {
  const normalized = message.toLowerCase();
  return ["my collection", "saved products", "list collection", "show collection"].some((phrase) =>
    normalized.includes(phrase)
  );
}

function wantsCirclePost(message) {
  const normalized = message.toLowerCase();
  return ["circle", "post", "share", "community", "friends"].some((token) =>
    normalized.includes(token)
  );
}

function draftCirclePost(message, products) {
  if (!products.length) {
    return "I am still looking for the right products. What budget, recipient, or use case should I optimize for?";
  }

  const names = products
    .slice(0, 3)
    .map((product) => product.name)
    .join(", ");

  return [
    `I am comparing a shortlist for this shopping need: ${message}`,
    "",
    `Top candidates: ${names}.`,
    "Which one would you pick, and what tradeoff should I check before buying? #GenPark #SocialShopping",
  ].join("\n");
}

function buildAnswer(products, budget, category, wantsCircle) {
  const context = [];
  if (budget !== null) context.push(`budget $${budget}`);
  if (category) context.push(category);

  const contextText = context.length ? ` for ${context.join(" and ")}` : "";
  let answer = `I found a ranked shortlist${contextText}:\n${summarizeProducts(products)}`;

  if (products.length) {
    answer += "\n\nI saved the top candidates to the demo collection so the workflow is reproducible.";
  }
  if (wantsCircle) {
    answer += "\n\nI also drafted an approval-gated Circle community post and am waiting for explicit confirmation.";
  }

  return answer;
}
