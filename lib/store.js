const state =
  globalThis.__genparkAgentState ||
  (globalThis.__genparkAgentState = {
    sessions: new Map(),
    collections: new Map(),
    posts: [],
    traces: [],
  });

function now() {
  return new Date().toISOString();
}

function sessionKey(userId, sessionId) {
  return `${userId}:${sessionId}`;
}

function collectionFor(userId) {
  if (!state.collections.has(userId)) {
    state.collections.set(userId, new Map());
  }
  return state.collections.get(userId);
}

export function touchSession(userId, sessionId, { lastMessage = null, pendingAction } = {}) {
  const key = sessionKey(userId, sessionId);
  const existing = state.sessions.get(key) || {};
  state.sessions.set(key, {
    ...existing,
    user_id: userId,
    session_id: sessionId,
    last_message: lastMessage ?? existing.last_message ?? null,
    pending_action: pendingAction === undefined ? existing.pending_action || null : pendingAction,
    updated_at: now(),
  });
}

export function getPendingAction(userId, sessionId) {
  return state.sessions.get(sessionKey(userId, sessionId))?.pending_action || null;
}

export function setPendingAction(userId, sessionId, action) {
  touchSession(userId, sessionId, { pendingAction: action });
}

export function clearPendingAction(userId, sessionId) {
  touchSession(userId, sessionId, { pendingAction: null });
}

export function addToCollection(userId, product) {
  const collection = collectionFor(userId);
  const inserted = !collection.has(product.id);
  collection.set(product.id, {
    ...product,
    saved_at: collection.get(product.id)?.saved_at || now(),
  });
  return inserted;
}

export function listCollection(userId) {
  return Array.from(collectionFor(userId).values()).sort((a, b) =>
    String(b.saved_at).localeCompare(String(a.saved_at))
  );
}

export function savePost(userId, content, status, postUrl = null, details = {}) {
  const post = {
    id: state.posts.length + 1,
    user_id: userId,
    content,
    status,
    post_url: postUrl,
    details,
    created_at: now(),
  };
  state.posts.push(post);
  return post;
}

export function saveTrace(userId, sessionId, message, response) {
  state.traces.push({
    id: state.traces.length + 1,
    user_id: userId,
    session_id: sessionId,
    message,
    response,
    created_at: now(),
  });
}

export function storeStats() {
  return {
    sessions: state.sessions.size,
    users_with_collections: state.collections.size,
    posts: state.posts.length,
    traces: state.traces.length,
  };
}
