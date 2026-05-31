import { NextResponse } from "next/server";
import { health } from "../../../lib/agent.js";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(health());
}
