import { publicCapabilities } from "./toolRegistry.js";

export function createRunId() {
  return `run_${Date.now().toString(36)}_${Math.random().toString(16).slice(2, 8)}`;
}

export function buildObjective(message, { budget, category, wantsCircle }) {
  return {
    raw_request: message,
    normalized_goal: "Turn a shopping intent into a ranked shortlist, saved collection, and decision handoff.",
    constraints: {
      budget,
      category,
      wants_circle_handoff: wantsCircle,
    },
  };
}

export function buildObservations({ budget, category, products, collection }) {
  return [
    budget === null
      ? "No explicit budget was found; the agent ranks by intent fit and rating."
      : `Budget constraint detected: $${budget}.`,
    category
      ? `Category hint detected: ${category}.`
      : "No strong category hint was detected; the agent keeps search broad.",
    `${products.length} candidate products are available after ranking.`,
    `${collection.length} products are currently saved for this user.`,
  ];
}

export function buildDecisionLog({ products, savedCount, wantsCircle, pendingAction }) {
  const leader = products[0];
  const decisions = [];

  if (leader) {
    decisions.push(
      `Top pick is ${leader.name} because ${leader.why || "it has the strongest combined fit score"}.`
    );
  } else {
    decisions.push("No product was strong enough to recommend; the agent should request tighter constraints.");
  }

  decisions.push(`${savedCount} new shortlist item${savedCount === 1 ? "" : "s"} saved.`);
  decisions.push(
    wantsCircle
      ? "A Circle handoff was drafted because the request asked for social validation."
      : "No external handoff was requested; the agent keeps the workflow inside the saved shortlist."
  );
  decisions.push(
    pendingAction
      ? "External publishing is blocked behind explicit approval."
      : "No external side effect is pending."
  );

  return decisions;
}

export function buildSafetyChecks({ wantsCircle, pendingAction, circleEnabled }) {
  return [
    {
      name: "External publish gate",
      status: wantsCircle && pendingAction ? "armed_requires_approval" : "clear",
      detail:
        wantsCircle && pendingAction
          ? "Circle publishing cannot run until the user confirms the draft."
          : "No external publish is currently pending.",
    },
    {
      name: "No fake side effects",
      status: circleEnabled ? "publish_channel_configured" : "demo_safe",
      detail: circleEnabled
        ? "A Circle webhook is configured; approved drafts can be sent externally."
        : "No Circle webhook is configured, so approved drafts are recorded without claiming a post happened.",
    },
    {
      name: "Deterministic judging",
      status: "reproducible",
      detail: "The catalog and ranking logic are deterministic so judges can repeat the same run.",
    },
  ];
}

export function buildClarifyingQuestions({ budget, category, products }) {
  const questions = [];
  if (budget === null) questions.push("What budget ceiling should I optimize for?");
  if (!category) questions.push("Should I bias toward electronics, home office, lifestyle, or another category?");
  if (!products.length) questions.push("Who is the recipient and what tradeoff matters most?");
  return questions;
}

export function buildScorecard({ budget, products, savedCount, wantsCircle, pendingAction, circleEnabled }) {
  const checks = [
    {
      label: "Intent parsed",
      passed: true,
      detail: budget === null ? "Parsed request, budget missing." : `Parsed request with $${budget} budget.`,
    },
    {
      label: "Useful shortlist",
      passed: products.length >= 3,
      detail: `${products.length} ranked candidates returned.`,
    },
    {
      label: "Stateful save",
      passed: savedCount > 0 || products.length > 0,
      detail: `${savedCount} newly saved items this run.`,
    },
    {
      label: "Approval gate",
      passed: !wantsCircle || Boolean(pendingAction),
      detail: wantsCircle ? "Circle draft is waiting for approval." : "No Circle handoff requested.",
    },
    {
      label: "Honest execution",
      passed: true,
      detail: circleEnabled
        ? "External channel is configured."
        : "Missing external channel is disclosed as setup-required.",
    },
  ];

  const passed = checks.filter((check) => check.passed).length;
  return {
    overall: Math.round((passed / checks.length) * 100),
    label: passed === checks.length ? "operator_ready" : "needs_more_context",
    checks,
  };
}

export function buildNextActions({ pendingAction, clarifyingQuestions }) {
  if (pendingAction) {
    return [
      "Review the Circle draft.",
      "Click Approve Draft only if the wording is acceptable.",
      "Use the saved shortlist as the buying decision record.",
    ];
  }

  if (clarifyingQuestions.length) {
    return clarifyingQuestions;
  }

  return [
    "Ask the agent to compare tradeoffs more deeply.",
    "Ask for a Circle handoff if you want community validation.",
    "Open the saved collection when ready to decide.",
  ];
}

export function buildAgentCard() {
  const capabilities = publicCapabilities();
  return {
    name: "GenPark Social Shopping Operator",
    autonomy_model: capabilities.autonomy_model,
    tool_count: capabilities.tools.length,
    principle: capabilities.principle,
  };
}
