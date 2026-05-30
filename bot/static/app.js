const state = {
  userId: localStorage.getItem("ucws_user_id") || `demo_${crypto.randomUUID().slice(0, 8)}`,
  sessionId: localStorage.getItem("ucws_session_id") || crypto.randomUUID(),
  pendingAction: null,
};

localStorage.setItem("ucws_user_id", state.userId);
localStorage.setItem("ucws_session_id", state.sessionId);

const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const answerText = document.querySelector("#answerText");
const draftPost = document.querySelector("#draftPost");
const products = document.querySelector("#products");
const productCount = document.querySelector("#productCount");
const planList = document.querySelector("#planList");
const toolCalls = document.querySelector("#toolCalls");
const sendButton = document.querySelector("#sendButton");
const confirmButton = document.querySelector("#confirmButton");
const healthStatus = document.querySelector("#healthStatus");
const metricProducts = document.querySelector("#metricProducts");
const metricSaved = document.querySelector("#metricSaved");
const metricTools = document.querySelector("#metricTools");
const metricState = document.querySelector("#metricState");

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await runAgent(input.value);
});

confirmButton.addEventListener("click", async () => {
  await runAgent("confirm post");
});

async function runAgent(message) {
  if (!message.trim()) return;
  setLoading(true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        user_id: state.userId,
        session_id: state.sessionId,
        message,
      }),
    });
    const data = await response.json();
    renderResponse(data);
  } catch (error) {
    answerText.textContent = `Request failed: ${error.message}`;
  } finally {
    setLoading(false);
  }
}

function renderResponse(data) {
  state.pendingAction = data.pending_action || null;
  answerText.textContent = data.answer || data.error || "No answer returned.";
  confirmButton.hidden = !state.pendingAction;
  metricProducts.textContent = String((data.products || []).length);
  metricSaved.textContent = String((data.collection || []).length);
  metricTools.textContent = String((data.tool_calls || []).length);
  metricState.textContent = state.pendingAction ? "pending" : data.post?.status || "ready";

  if (data.draft_post) {
    draftPost.hidden = false;
    draftPost.textContent = data.draft_post;
  } else if (data.post?.content) {
    draftPost.hidden = false;
    draftPost.textContent = data.post.content;
  } else {
    draftPost.hidden = true;
    draftPost.textContent = "";
  }

  renderPlan(data.plan || []);
  renderTools(data.tool_calls || []);
  renderProducts(data.products || data.collection || []);
}

function renderPlan(plan) {
  planList.innerHTML = "";
  plan.forEach((step) => {
    const item = document.createElement("li");
    item.textContent = step;
    planList.appendChild(item);
  });
}

function renderTools(calls) {
  toolCalls.innerHTML = "";
  calls.forEach((call) => {
    const row = document.createElement("article");
    row.className = "toolCall";
    row.innerHTML = `
      <div class="toolTop">
        <strong>${escapeHtml(call.tool || "tool")}</strong>
        <span>${escapeHtml(call.status || "unknown")}</span>
      </div>
      <p>${escapeHtml(call.summary || "")}</p>
    `;
    toolCalls.appendChild(row);
  });
}

function renderProducts(items) {
  products.innerHTML = "";
  productCount.textContent = `${items.length} ${items.length === 1 ? "item" : "items"}`;

  items.forEach((product, index) => {
    const card = document.createElement("article");
    card.className = "productCard";
    card.innerHTML = `
      <div class="productMedia">
        <img src="${escapeAttr(product.image_url || "")}" alt="${escapeAttr(product.name || product.product_name || "Product")}">
        <span class="rankBadge">#${index + 1}</span>
      </div>
      <div class="productBody">
        <div class="productTop">
          <h3>${escapeHtml(product.name || product.product_name || product.id)}</h3>
          <span>$${Number(product.price || 0).toFixed(2)}</span>
        </div>
        <span class="category">${escapeHtml(product.category || "Saved item")}</span>
        <p>${escapeHtml(product.why || product.description || "")}</p>
        <div class="tags">${(product.tags || []).slice(0, 4).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>
      </div>
    `;
    products.appendChild(card);
  });
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  sendButton.textContent = isLoading ? "Running..." : "Run Agent";
  if (isLoading) {
    metricState.textContent = "running";
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

async function loadHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    healthStatus.textContent = `${data.status} - ${data.mode}`;
  } catch {
    healthStatus.textContent = "runtime unavailable";
  }
}

loadHealth();
