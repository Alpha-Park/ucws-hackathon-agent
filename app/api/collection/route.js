import { NextResponse } from "next/server";
import { listCollection } from "../../../lib/store.js";

export const dynamic = "force-dynamic";

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get("user_id") || "demo";
  const collection = listCollection(userId);

  return NextResponse.json({
    success: true,
    mode: "vercel_operator",
    user_id: userId,
    collection,
  });
}
