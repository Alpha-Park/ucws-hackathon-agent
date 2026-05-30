from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from bot.services import AgentService

app = Flask(__name__, static_folder="static", template_folder="templates")
service = AgentService()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(service.health())


@app.post("/chat")
async def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    user_id = data.get("user_id") or request.headers.get("X-User-Id") or "demo_user"
    session_id = data.get("session_id") or request.headers.get("X-Session-Id") or "demo_session"

    if not user_message:
        return jsonify({"success": False, "error": "message is required"}), 400

    response = await service.process_request(user_id, session_id, user_message)
    return jsonify(response)


@app.get("/collection")
def collection():
    user_id = request.args.get("user_id") or request.headers.get("X-User-Id") or "demo_user"
    return jsonify(
        {
            "success": True,
            "user_id": user_id,
            "items": service.store.list_collection(user_id),
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=False)
