import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";
import type { AgentCommandConsole } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const data = await backendFetch<AgentCommandConsole>("/api/v1/agents");
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load agents";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
