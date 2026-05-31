"""Optional Google ADK agent definition.

The Flask demo uses `AgentService` for a deterministic, auditable workflow. This
ADK definition is kept so the same tools can be mounted in a Google ADK runtime
when credentials and dependencies are configured.
"""

from bot.tools.circle import post_to_circle
from bot.tools.collection import add_to_collection, list_collection, remove_from_collection
from bot.tools.recommend import get_recommendations
from bot.tools.search import get_trending_products, search_products

try:
    from google.adk.agents import Agent
except ImportError:  # pragma: no cover - lets local demo run before ADK install
    Agent = None


if Agent:
    root_agent = Agent(
        name="genpark_social_shopping_agent",
        model="gemini-2.0-flash",
        description=(
            "A GenPark social shopping operator that searches products, compares candidates, "
            "saves shortlists, drafts approval-gated Circle posts, and waits for explicit approval before side effects."
        ),
        instruction="""You are a social shopping operator for GenPark.ai.

Help users turn a shopping need into a concrete shortlist and a shareable, approval-gated Circle post.

Rules:
- Search and rank products before recommending.
- Explain budget fit, relevant features, and tradeoffs.
- Save useful candidates to collection when asked.
- Draft posts for Circle as a social handoff, but do not publish until the user explicitly confirms.
- Never claim a side effect succeeded unless the tool result says success=true.
""",
        tools=[
            post_to_circle,
            add_to_collection,
            list_collection,
            remove_from_collection,
            get_recommendations,
            search_products,
            get_trending_products,
        ],
    )
else:
    root_agent = None
