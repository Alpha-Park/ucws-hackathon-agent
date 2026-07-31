import { NextResponse } from "next/server";
import { publicCapabilities } from "../../../lib/toolRegistry.js";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    success: true,
    mode: "vercel_operator",
    capabilities: publicCapabilities(),
  });
}
