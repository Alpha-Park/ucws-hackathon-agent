"use client";

import { useEffect, useMemo, useState } from "react";

const DEMO_PROMPT =
  "I need a globally useful gift for a remote worker under $220. Compare the best options, save the shortlist, and draft a Circle post asking the community which one I should buy.";

const EXAMPLES = [
  {
    label: "Remote worker gift",
    prompt: DEMO_PROMPT,
  },
  {
    label: "Smart home under $160",
    prompt:
      "Recommend smart home products under $160, save the shortlist, and draft a Circle post asking friends to vote.",
  },
  {
    label: "Show collection",
    prompt: "Show my collection",
  },
];

const DEFAULT_PLAN = [
  "Parse the shopping intent, budget, and category hints.",
  "Search the product catalog with budget-aware ranking.",
  "Compare candidates and explain the tradeoffs.",
  "Save the strongest shortlist to the user's collection.",
  "Draft an approval-gated Circle community handoff and wait for explicit confirmation.",
];

function createClientId(prefix) {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `${prefix}_${crypto.randomUUID().slice(0, 8)}`;
  }
  return `${prefix}_${Math.random().toString(16).slice(2, 10)}`;
}

export default function Home() {
  const [identity, setIdentity] = useState({ userId: "demo", sessionId: "demo" });
  const [message, setMessage] = useState(DEMO_PROMPT);
  const [answer, setAnswer] = useState(
    "Ready. Run the agent to generate a ranked shortlist, saved collection, and approval-gated Circle draft."
  );
  const [draftPost, setDraftPost] = useState("");
  const [products, setProducts] = useState([]);
  const [collection, setCollection] = useState([]);
  const [plan, setPlan] = useState(DEFAULT_PLAN);
  const [toolCalls, setToolCalls] = useState([]);
  const [observations, setObservations] = useState([]);
  const [decisionLog, setDecisionLog] = useState([]);
  const [safetyChecks, setSafetyChecks] = useState([]);
  const [nextActions, setNextActions] = useState([]);
  const [scorecard, setScorecard] = useState({ overall: 0, label: "not_run", checks: [] });
  const [agentCard, setAgentCard] = useState(null);
  const [runId, setRunId] = useState("");
  const [pendingAction, setPendingAction] = useState(null);
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState("checking runtime");

  const metrics = useMemo(
    () => ({
      products: products.length,
      saved: collection.length,
      tools: toolCalls.length,
      state: loading ? "running" : pendingAction ? "pending" : post?.status || "ready",
    }),
    [collection.length, loading, pendingAction, post?.status, products.length, toolCalls.length]
  );

  useEffect(() => {
    const storedUserId =
      window.localStorage.getItem("ucws_user_id") || createClientId("demo");
    const storedSessionId =
      window.localStorage.getItem("ucws_session_id") || createClientId("session");
    const nextIdentity = { userId: storedUserId, sessionId: storedSessionId };

    window.localStorage.setItem("ucws_user_id", storedUserId);
    window.localStorage.setItem("ucws_session_id", storedSessionId);
    setIdentity(nextIdentity);

    fetch("/api/health")
      .then((response) => response.json())
      .then((data) => setHealthStatus(`${data.status} - ${data.mode}`))
      .catch(() => setHealthStatus("runtime unavailable"));

    if (new URLSearchParams(window.location.search).get("demo") === "1") {
      window.setTimeout(() => runAgent(DEMO_PROMPT, nextIdentity), 300);
    }
  }, []);

  async function runAgent(nextMessage, activeIdentity = identity) {
    const cleanMessage = nextMessage.trim();
    if (!cleanMessage) return;

    setLoading(true);
    setPost(null);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: activeIdentity.userId,
          session_id: activeIdentity.sessionId,
          message: cleanMessage,
        }),
      });
      const data = await response.json();
      renderResponse(data);
    } catch (error) {
      setAnswer(`Request failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  function renderResponse(data) {
    setPendingAction(data.pending_action || null);
    setAnswer(data.answer || data.error || "No answer returned.");
    setDraftPost(data.draft_post || data.post?.content || "");
    setProducts((currentProducts) => data.products || data.collection || currentProducts);
    setCollection((currentCollection) => data.collection || data.products || currentCollection);
    setPlan(data.plan || DEFAULT_PLAN);
    setToolCalls(data.tool_calls || []);
    setObservations(data.observations || []);
    setDecisionLog(data.decision_log || []);
    setSafetyChecks(data.safety_checks || []);
    setNextActions(data.next_actions || (data.next_action ? [data.next_action] : []));
    setScorecard(data.scorecard || { overall: 0, label: "not_run", checks: [] });
    setAgentCard(data.agent_card || null);
    setRunId(data.run_id || "");
    setPost(data.post || null);
  }

  function handleSubmit(event) {
    event.preventDefault();
    runAgent(message);
  }

  return (
    <main>
      <section className="hero">
        <nav className="topNav" aria-label="Product status">
          <div className="brandCluster">
            <span className="brandMark" aria-hidden="true">
              <img src="/logo.jpg" alt="" />
            </span>
            <div>
              <strong>GenPark Social Shopping Agent</strong>
              <span>UCWS Singapore Hackathon 2026</span>
            </div>
          </div>
          <span className="status">{healthStatus}</span>
        </nav>
        <div className="heroInner">
          <p className="eyebrow">Agent Track / Approval-Gated Commerce</p>
          <h1>Intent becomes a social shopping operation.</h1>
          <p className="heroCopy">
            Not a shopping chatbot. A social shopping operator that turns buyer intent into a
            ranked shortlist, saved collection, and Circle draft that waits for approval.
          </p>
        </div>
      </section>

      <section className="commandDock" aria-label="Agent command center">
        <div className="commandTop">
          <div>
            <p className="sectionKicker">Live Agent Run</p>
            <h2>Command the shopping workflow</h2>
          </div>
          <div className="metricStrip" aria-label="Agent telemetry">
            <div>
              <span>{metrics.products}</span>
              <small>ranked</small>
            </div>
            <div>
              <span>{metrics.saved}</span>
              <small>saved</small>
            </div>
            <div>
              <span>{metrics.tools}</span>
              <small>tools</small>
            </div>
            <div>
              <span>{metrics.state}</span>
              <small>state</small>
            </div>
          </div>
        </div>

        <form className="commandForm" onSubmit={handleSubmit}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            aria-label="Shopping request"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Running..." : "Run Agent"}
          </button>
        </form>

        <div className="examples" aria-label="Demo prompts">
          {EXAMPLES.map((example) => (
            <button
              type="button"
              key={example.label}
              onClick={() => {
                setMessage(example.prompt);
              }}
            >
              {example.label}
            </button>
          ))}
          {pendingAction ? (
            <button
              type="button"
              className="secondary"
              disabled={loading}
              onClick={() => runAgent("confirm post")}
            >
              Approve Draft
            </button>
          ) : null}
        </div>
      </section>

      <section className="resultsLayout" aria-label="Agent result">
        <div className="storyColumn">
          <article className="answerBlock">
            <div className="sectionHeader">
              <div>
                <p className="sectionKicker">Decision Brief</p>
                <h2>What the agent decided</h2>
              </div>
            </div>
            <pre className="answerText">{answer}</pre>
          </article>

          <article className="draftBlock">
            <div className="sectionHeader">
              <div>
                <p className="sectionKicker">Circle Handoff</p>
                <h2>Approval-gated community post</h2>
              </div>
            </div>
            <div className={`draft ${draftPost ? "" : "emptyDraft"}`}>
              {draftPost || "Run a prompt that asks for a Circle post to generate a draft."}
            </div>
            {post ? (
              <div className="postReceipt" aria-label="Approved post receipt">
                <div>
                  <strong>{post.status || "approved"}</strong>
                  <span>
                    {post.post_url
                      ? "Published through the configured Circle webhook."
                      : "Approved draft saved. No fake publish was claimed."}
                  </span>
                </div>
                {post.post_url ? (
                  <a href={post.post_url} target="_blank" rel="noreferrer">
                    Open post
                  </a>
                ) : null}
              </div>
            ) : null}
          </article>
        </div>

        <aside className="receiptColumn" aria-label="Execution receipt">
          <div className="receiptHeader">
            <p className="sectionKicker">Execution Receipt</p>
            <h2>Plan and tool trace</h2>
          </div>
          <ol className="planList">
            {plan.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>

          <div className="traceDivider" />

          <div className="toolCalls">
            {toolCalls.length ? (
              toolCalls.map((call, index) => (
                <article className="toolCall" key={`${call.tool}-${index}`}>
                  <div className="toolTop">
                    <strong>{call.tool || "tool"}</strong>
                    <span>{call.status || "unknown"}</span>
                  </div>
                  <p>{call.summary || ""}</p>
                </article>
              ))
            ) : (
              <article className="toolCall">
                <div className="toolTop">
                  <strong>waiting_for_run</strong>
                  <span>idle</span>
                </div>
                <p>Tool calls appear here after the agent executes.</p>
              </article>
            )}
          </div>

          <div className="traceDivider" />

          <section className="agentAudit" aria-label="Agent audit">
            <div className="auditTop">
              <div>
                <p className="sectionKicker">Operator Audit</p>
                <h2>Self-check and next move</h2>
              </div>
              <span className="scoreBadge">{scorecard.overall || 0}/100</span>
            </div>

            <div className="auditMeta">
              <span>{scorecard.label}</span>
              <span>{agentCard?.autonomy_model || "supervised_operator"}</span>
              {runId ? <span>{runId}</span> : null}
            </div>

            <AuditList title="Observations" items={observations} />
            <AuditList title="Decisions" items={decisionLog} />

            {safetyChecks.length ? (
              <div className="auditGroup">
                <strong>Safety</strong>
                <ul>
                  {safetyChecks.map((check) => (
                    <li key={check.name}>
                      <span>{check.name}</span>
                      <small>{check.status}</small>
                      <p>{check.detail}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <AuditList title="Next Actions" items={nextActions} />
          </section>
        </aside>
      </section>

      <section className="productSection" aria-label="Ranked products">
        <div className="sectionHeader">
          <div>
            <p className="sectionKicker">Saved Shortlist</p>
            <h2>Products the agent can explain and save</h2>
          </div>
          <span className="countPill">
            {products.length} {products.length === 1 ? "item" : "items"}
          </span>
        </div>
        <div className="productGrid">
          {products.map((product, index) => (
            <article className="productCard" key={product.id || `${product.name}-${index}`}>
              <div className="productMedia">
                <img src={product.image_url || ""} alt={product.name || "Product"} />
                <span className="rankBadge">#{index + 1}</span>
              </div>
              <div className="productBody">
                <div className="productTop">
                  <h3>{product.name || product.product_name || product.id}</h3>
                  <span>${Number(product.price || 0).toFixed(2)}</span>
                </div>
                <span className="category">{product.category || "Saved item"}</span>
                <p>{product.why || product.description || ""}</p>
                <div className="tags">
                  {(product.tags || []).slice(0, 4).map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

function AuditList({ title, items }) {
  if (!items?.length) return null;

  return (
    <div className="auditGroup">
      <strong>{title}</strong>
      <ul>
        {items.map((item) => (
          <li key={item}>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
