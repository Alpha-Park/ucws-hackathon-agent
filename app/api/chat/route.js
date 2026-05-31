import { NextResponse } from "next/server";
import { processRequest } from "../../../lib/agent.js";

export const dynamic = "force-dynamic";

export async function POST(request) {
  try {
    const body = await request.json();
    const message = String(body.message || "").trim();

    if (!message) {
      return NextResponse.json(
        { success: false, error: "message is required", mode: "vercel_operator" },
        { status: 400 }
      );
    }

    const response = await processRequest({
      userId: body.user_id || body.userId || "demo",
      sessionId: body.session_id || body.sessionId || "demo",
      message,
    });

    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unexpected agent error",
        mode: "vercel_operator",
      },
      { status: 500 }
    );
  }
}
