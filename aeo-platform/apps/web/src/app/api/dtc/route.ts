import { NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";
import type { DTCDashboardData } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const token = getAccessToken();
    const data = await backendFetch<DTCDashboardData>("/api/v1/dtc/dashboard", {
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to load DTC dashboard";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
