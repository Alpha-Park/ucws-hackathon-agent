# UCWS Singapore Hackathon 2026 Submission Brief

## One-Line Pitch

This is not a shopping chatbot. It is a social shopping operator that turns intent into a saved shortlist and an approval-gated community post.

## Problem

Online shopping discovery is fragmented: users search products, compare options, save candidates, and then ask friends or communities for validation in separate tools. That creates friction and makes recommendations hard to trust.

## Product

GenPark Social Shopping Agent converts one natural-language shopping intent into a complete social-shopping workflow:

1. Parse buyer intent, budget, and category hints.
2. Search and rank products.
3. Explain why the top candidates fit.
4. Save the shortlist to the user's collection.
5. Draft a GenPark Circle community post.
6. Wait for explicit approval before any publishing side effect.

## Why It Fits The Agent Track

- It executes a multi-step workflow rather than returning a single chat answer.
- It uses tools for search, ranking, collection persistence, Circle handoff, and optional publishing.
- It keeps state in SQLite: sessions, collections, pending approvals, posts, and traces.
- It exposes its plan and tool calls for auditability.
- It treats external side effects safely: no fake publish success.

## 60-Second Demo Script

1. Open the app and point to the prefilled prompt.
2. Click `Run Agent`.
3. Show the telemetry: ranked products, saved items, tool count, pending state.
4. Show the decision brief: products are ranked with budget and intent reasons.
5. Show the Circle draft: the agent turns the shortlist into a community handoff.
6. Show the execution receipt: plan and tool calls are visible.
7. Click `Approve Draft`.
8. Explain that without GenPark browser credentials, the approved draft is saved as `drafted_requires_setup` instead of pretending it was posted.

## Suggested Demo Prompt

```text
I need a globally useful gift for a remote worker under $220. Compare the best options, save the shortlist, and draft a Circle post asking the community which one I should buy.
```

## Evaluation Mapping

### Community Vote

- Clear story: shopping intent becomes a social decision loop.
- Easy to understand from the first screen.
- Shareable output: Circle draft built from ranked products.

### AI Evaluation

- Runnable Flask app with deterministic local catalog.
- Structured API responses with plan, tool calls, products, collection, draft, and pending action.
- Tests cover budget inference, ranking, pending approvals, and no fake publish.
- README includes screenshot, run steps, architecture, API shape, and limitations.

### Expert Judges

- Real product value: reduces shopping decision friction and adds social validation.
- Technical execution: stateful agent workflow, persistent collection, approval-gated side effects.
- Commercial potential: can become a GenPark-native shopping operator tied to catalog, Circle, and user collections.
- Global scalability: buyer intent, gifting, and community validation are global user behaviors.

## What Is Real Today

- Agent workflow orchestration
- Product ranking over a deterministic catalog
- SQLite-backed sessions, collections, approvals, posts, and traces
- Approval-gated Circle handoff
- Optional browser publishing path when credentials are configured
- Web UI and API

## What Would Make It Production-Grade

- Replace local catalog with GenPark product/search API.
- Use real user authentication and account-linked collections.
- Replace browser automation with official Circle publishing APIs when available.
- Add hosted deployment and public demo URL.
- Add richer product evidence: reviews, availability, images, shipping, and price history.

