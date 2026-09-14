import { NextResponse } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { backendFetch } from "@/lib/backend";
import type { TenantInfo } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const token = getAccessToken();
    const data = await backendFetch<TenantInfo>("/api/v1/tenants/me", {
      accessToken: token,
    });
    return NextResponse.json({ data });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to load tenant info";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
