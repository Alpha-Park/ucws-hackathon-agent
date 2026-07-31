export const TOOL_REGISTRY = [
  {
    name: "parse_intent",
    purpose: "Extract buyer goal, budget, category hints, and social-sharing intent.",
    side_effect: "none",
    approval: "not_required",
  },
  {
    name: "search_products",
    purpose: "Retrieve catalog candidates that satisfy the parsed constraints.",
    side_effect: "none",
    approval: "not_required",
  },
  {
    name: "rank_products",
    purpose: "Score candidates against intent, budget, match terms, and product rating.",
    side_effect: "none",
    approval: "not_required",
  },
  {
    name: "save_to_collection",
    purpose: "Persist the shortlist so the user can return to it after the agent run.",
    side_effect: "local_state",
    approval: "implicit",
  },
  {
    name: "draft_circle_post",
    purpose: "Create a community handoff that asks humans to help choose between candidates.",
    side_effect: "none",
    approval: "not_required",
  },
  {
    name: "post_to_circle",
    purpose: "Publish an approved community post through the configured Circle channel.",
    side_effect: "external_publish",
    approval: "explicit_required",
  },
  {
    name: "self_evaluate_run",
    purpose: "Audit completeness, safety, assumptions, and next best action before responding.",
    side_effect: "none",
    approval: "not_required",
  },
];

export function publicCapabilities() {
  return {
    autonomy_model: "supervised_operator",
    principle:
      "The agent may search, rank, save, draft, and audit autonomously; external publishing requires explicit user approval.",
    tools: TOOL_REGISTRY,
  };
}
